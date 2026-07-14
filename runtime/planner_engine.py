import logging
import time
from typing import Any, AsyncIterator

from agents.skill_planner.factory import SkillPlannerAgentFactory
from runtime.engine import (
    _build_attachment_context,
    _extract_final_response,
    _extract_reasoning_text,
    _is_ai_message,
    _merge_text_delta,
    _message_content_text,
    _split_stream_part,
    _summarize_event,
)
from runtime.workspace_manager import WorkspaceManager


log = logging.getLogger("flow.planner_engine")


class PlannerEngine:
    def __init__(self) -> None:
        self.agent = None
        self.initialized = False

    async def initialize(self) -> None:
        if self.initialized:
            return

        self.agent = SkillPlannerAgentFactory.create_agent()
        self.initialized = True
        log.info("Planner Runtime initialized")

    def _prepare_request(
        self,
        message: str,
        thread_id: str,
        user_id: str,
        request_id: str,
        attachments: list[str] | None = None,
    ) -> tuple[dict[str, list[dict[str, str]]], WorkspaceManager, dict[str, tuple[int, int]]]:
        workspace = WorkspaceManager()
        normalized_attachments: list[str] = []
        for item in attachments or []:
            if not isinstance(item, str):
                continue
            path = item.strip()
            if not path:
                continue
            try:
                normalized_attachments.append(workspace.to_user_virtual_path(user_id, path))
            except ValueError:
                continue

        attachment_context = _build_attachment_context(normalized_attachments, user_id, workspace)
        input_content = message
        if attachment_context:
            input_content = f"{message}\n\n{attachment_context}"
            log.info(
                "planner attachments injected request_id=%s thread_id=%s attachment_count=%s attachments=%s",
                request_id,
                thread_id,
                len(normalized_attachments),
                ",".join(normalized_attachments),
            )

        # PlannerEngine intentionally does not persist planner chats.
        # history = get_content_messages(thread_id)
        # if not history:
        #     create_thread(user_id, thread_id, message[:30])
        # update_thread_time(thread_id)
        # save_message(user_id, thread_id, "user", message)

        return {"messages": [{"role": "user", "content": input_content}]}, workspace, workspace.snapshot_downloadables()

    @staticmethod
    def _config(thread_id: str, user_id: str) -> dict[str, dict[str, str]]:
        return {"configurable": {"thread_id": thread_id, "user_id": user_id}}

    def _require_agent(self):
        if self.agent is None:
            raise RuntimeError("planner agent is not initialized")
        return self.agent

    async def run(
        self,
        message: str,
        thread_id: str = "default",
        user_id: str = "default_user",
        attachments: list[str] | None = None,
        request_id: str | None = None,
    ) -> str:
        request_id = request_id or "-"
        input_message, workspace, before_outputs = self._prepare_request(
            message, thread_id, user_id, request_id, attachments
        )
        events: list[Any] = []
        agent = self._require_agent()

        log.info("planner request started request_id=%s thread_id=%s user_id=%s", request_id, thread_id, user_id)
        async for event in agent.astream(input_message, config=self._config(thread_id, user_id)):
            events.append(event)

        changed_files = workspace.detect_changed_downloadables(before_outputs)
        if changed_files:
            log.info("planner artifacts detected request_id=%s files=%s", request_id, ",".join(changed_files))

        answer, _ = _extract_final_response(events)
        # PlannerEngine intentionally does not persist planner chats.
        # save_message(user_id, thread_id, "assistant", answer)
        log.info("planner request finished request_id=%s answer_chars=%s", request_id, len(answer))
        return answer

    async def stream_chat(
        self,
        message: str,
        thread_id: str = "default",
        user_id: str = "default_user",
        attachments: list[str] | None = None,
        request_id: str | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        request_id = request_id or "-"
        input_message, workspace, before_outputs = self._prepare_request(
            message, thread_id, user_id, request_id, attachments
        )
        agent = self._require_agent()
        started = time.time()
        latest_answer = ""
        latest_reasoning = ""
        token_usage = None
        update_events: list[Any] = []
        event_count = 0

        yield {
            "type": "status",
            "stage": "started",
            "request_id": request_id,
            "thread_id": thread_id,
            "user_id": user_id,
        }

        async for stream_part in agent.astream(
            input_message,
            config=self._config(thread_id, user_id),
            stream_mode=["messages", "updates"],
        ):
            mode, payload = _split_stream_part(stream_part)
            if mode == "updates":
                update_events.append(payload)
                event_count += 1
                summary = _summarize_event(payload)
                yield {
                    "type": "agent_event",
                    "request_id": request_id,
                    "index": event_count,
                    "nodes": summary["nodes"],
                    "message_types": summary["message_types"],
                    "tool_calls": summary["tool_calls"],
                    "preview": summary["preview"],
                }
                continue

            if mode != "messages" or not isinstance(payload, tuple) or len(payload) != 2:
                continue

            response, metadata = payload
            if not _is_ai_message(response):
                continue

            response_metadata = getattr(response, "response_metadata", None) or {}
            token_usage = response_metadata.get("token_usage") or token_usage

            reasoning_delta, latest_reasoning = _merge_text_delta(
                latest_reasoning,
                _extract_reasoning_text(response),
            )
            if reasoning_delta:
                yield {
                    "type": "reasoning_delta",
                    "request_id": request_id,
                    "delta": reasoning_delta,
                    "content": latest_reasoning,
                    "node": metadata.get("langgraph_node") if isinstance(metadata, dict) else None,
                }

            if getattr(response, "tool_call_chunks", None) or getattr(response, "tool_calls", None):
                continue

            answer_delta, latest_answer = _merge_text_delta(
                latest_answer,
                _message_content_text(getattr(response, "content", "")),
            )
            if answer_delta:
                yield {
                    "type": "message_delta",
                    "request_id": request_id,
                    "delta": answer_delta,
                    "content": latest_answer,
                    "node": metadata.get("langgraph_node") if isinstance(metadata, dict) else None,
                }

        if not latest_answer and update_events:
            latest_answer, fallback_usage = _extract_final_response(update_events)
            token_usage = token_usage or fallback_usage

        changed_files = workspace.detect_changed_downloadables(before_outputs)
        if changed_files:
            log.info("planner artifacts detected request_id=%s files=%s", request_id, ",".join(changed_files))
            yield {
                "type": "artifact",
                "request_id": request_id,
                "files": changed_files,
            }

        # PlannerEngine intentionally does not persist planner chats.
        # save_message(user_id, thread_id, "assistant", latest_answer)
        yield {
            "type": "done",
            "request_id": request_id,
            "content": latest_answer,
            "token_usage": token_usage,
        }
        log.info(
            "planner stream finished request_id=%s answer_chars=%s latency=%.2fs",
            request_id,
            len(latest_answer),
            time.time() - started,
        )

    async def shutdown(self) -> None:
        self.agent = None
        self.initialized = False
        log.info("Planner Runtime shutdown complete")
