from __future__ import annotations

import json
import logging
from typing import Any, AsyncIterator, Callable, Optional

from agents.subagent.workflow_advisor.schema import AdvisorChatRequest, AdvisorCanvasContext

from services.subagent.workflow_advisor.context_builder import summarize_canvas_dsl

log = logging.getLogger("flow.workflow_advisor")


class WorkflowAdvisorService:
    def __init__(
        self,
        advisor_agent: Any,
        skill_resolver: Optional[Callable[[str], Any]] = None,
    ):
        self.advisor_agent = advisor_agent
        self.skill_resolver = skill_resolver

    async def stream_chat(
        self,
        req: AdvisorChatRequest,
        request_id: str,
    ) -> AsyncIterator[dict]:
        """
        编排向导流式对话：
        - 构建 DSL 摘要上下文
        - 调用 advisor graph
        - 将模型输出流式转成 SSE
        """

        # 1) 编排向导会话ID -> thread_id
        thread_id = req.advisor_session_id

        log.info(
            "workflow advisor request request_id=%s user_id=%s workflow_id=%s advisor_session_id=%s",
            request_id,
            req.user_id,
            req.workflow_id,
            req.advisor_session_id,
        )

        # 2) 构建画板上下文
        canvas_ctx: AdvisorCanvasContext = summarize_canvas_dsl(
            req.canvas_dsl,
            workflow_id=req.workflow_id,
            selected_node_id=req.selected_node_id,
            skill_resolver=self.skill_resolver,
        )

        # 3) 组装给模型的用户输入
        user_payload = {
            "user_message": req.message,
            "workflow_id": req.workflow_id,
            "selected_node_id": req.selected_node_id,
            "canvas_context": canvas_ctx.model_dump(mode="json", exclude_none=True),
        }

        user_content = json.dumps(user_payload, ensure_ascii=False, indent=2)

        # 给前端一个开始事件
        yield {
            "type": "start",
            "request_id": request_id,
            "workflow_id": req.workflow_id,
            "advisor_session_id": req.advisor_session_id,
        }

        # 4) 调用 advisor graph
        #
        # 关键点：
        # - 用 astream，不用 stream_events
        # - stream_mode 建议先用 "messages"
        # - configurable 里传 thread_id/user_id/workflow_id
        #
        final_text_parts: list[str] = []

        async for chunk, metadata in self.advisor_agent.astream(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": user_content,
                    }
                ]
            },
            config={
                "configurable": {
                    "thread_id": thread_id,
                    "user_id": req.user_id,
                    "workflow_id": req.workflow_id,
                }
            },
            stream_mode="messages",
        ):
            text = self._extract_message_chunk_text(chunk)
            if not text:
                continue

            final_text_parts.append(text)
            yield {
                "type": "delta",
                "request_id": request_id,
                "delta": text,
            }

        final_text = "".join(final_text_parts).strip()

        yield {
            "type": "done",
            "request_id": request_id,
            "workflow_id": req.workflow_id,
            "advisor_session_id": req.advisor_session_id,
            "content": final_text,
        }

    def _extract_message_chunk_text(self, chunk: Any) -> str:
        """
        从 astream(stream_mode='messages') 返回的 chunk 中尽量提取文本。
        兼容不同消息块结构。
        """
        if chunk is None:
            return ""

        # 1) 直接是字符串
        if isinstance(chunk, str):
            return chunk

        # 2) 常见 AIMessageChunk / BaseMessageChunk
        content = getattr(chunk, "content", None)
        if isinstance(content, str):
            return content

        # 3) content 可能是 list[dict|str]
        if isinstance(content, list):
            texts: list[str] = []
            for item in content:
                if isinstance(item, str):
                    texts.append(item)
                elif isinstance(item, dict):
                    # 常见格式: {"type": "text", "text": "..."}
                    if item.get("type") == "text" and item.get("text"):
                        texts.append(item["text"])
            return "".join(texts)

        # 4) dict 兜底
        if isinstance(chunk, dict):
            c = chunk.get("content")
            if isinstance(c, str):
                return c
            if isinstance(c, list):
                texts: list[str] = []
                for item in c:
                    if isinstance(item, str):
                        texts.append(item)
                    elif isinstance(item, dict) and item.get("type") == "text" and item.get("text"):
                        texts.append(item["text"])
                return "".join(texts)

        return ""