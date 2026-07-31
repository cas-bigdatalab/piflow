import asyncio
import importlib.util
import json
import logging
from pathlib import Path
import time
from typing import Any, AsyncIterator

from agents.skill_planner.factory import SkillPlannerAgentFactory
from runtime.chat_store import get_chat_files_by_message
from runtime.engine import (
    _build_attachment_context,
    _extract_final_response,
    _extract_reasoning_text,
    _is_ai_message,
    _normalize_attachment_records,
    _merge_text_delta,
    _message_content_text,
    _split_stream_part,
    _summarize_event,
)
from runtime.workspace_manager import WorkspaceManager


log = logging.getLogger("flow.planner_engine")

PLANNER_EXECUTE_SPEC_MARKER = "__PIFLOW_PLANNER_EXECUTE_SPEC__"
_PLANNER_SKILL_SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "workspace"
    / "skills"
    / "planner"
    / "piflow-skill-generator_planner"
    / "scripts"
    / "generate_piflow_skill.py"
)


def _extract_execution_spec(answer: str) -> dict[str, Any] | None:
    if PLANNER_EXECUTE_SPEC_MARKER not in answer:
        return None

    _, raw_spec = answer.split(PLANNER_EXECUTE_SPEC_MARKER, 1)
    raw_spec = raw_spec.strip()
    if raw_spec.startswith("```json"):
        raw_spec = raw_spec.removeprefix("```json").strip()
    if raw_spec.endswith("```"):
        raw_spec = raw_spec[:-3].strip()

    spec = json.loads(raw_spec)
    if not isinstance(spec, dict):
        raise ValueError("planner execution spec must be a JSON object")
    return spec


def _generate_planner_skill(spec: dict[str, Any], thread_id: str) -> dict[str, Any]:
    if not _PLANNER_SKILL_SCRIPT.is_file():
        raise FileNotFoundError(f"planner skill entrypoint not found: {_PLANNER_SKILL_SCRIPT}")

    module_spec = importlib.util.spec_from_file_location("piflow_planner_skill", _PLANNER_SKILL_SCRIPT)
    if module_spec is None or module_spec.loader is None:
        raise RuntimeError("unable to load planner skill entrypoint")

    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    output_root = module.resolve_output_root(str(spec.get("output_root") or module.DEFAULT_OUTPUT_ROOT))
    return module.generate(spec, output_root, bool(spec.get("overwrite", False)), thread_id)


def _format_execution_result(result: dict[str, Any]) -> str:
    return "\n".join(
        part
        for part in (
            "Skill 已生成并注册。",
            f"- 目录：{result.get('skill_dir', '')}",
            f"- 定义：{result.get('skill_md', '')}",
            f"- DAG skill ID：{result.get('dag_skill_id') or '未返回'}",
        )
        if part
    )


def _skill_followup_prompt(result: dict[str, Any]) -> str:
    prompt = result.get("followup_prompt")
    return prompt.strip() if isinstance(prompt, str) else ""


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
        attachments: list[Any] | None = None,
        message_id: int | None = None,
    ) -> tuple[dict[str, list[dict[str, str]]], WorkspaceManager, dict[str, tuple[int, int]]]:
        workspace = WorkspaceManager()
        resolved_attachments: list[Any] = list(attachments or [])
        if message_id is not None:
            resolved_attachments.extend(get_chat_files_by_message(thread_id, str(message_id)))
        normalized_attachments = _normalize_attachment_records(resolved_attachments, user_id, workspace)
        attachment_context = _build_attachment_context(normalized_attachments, user_id, workspace)
        input_content = message
        if attachment_context:
            input_content = f"{message}\n\n{attachment_context}"
            log.info(
                "planner attachments injected request_id=%s thread_id=%s attachment_count=%s attachments=%s",
                request_id,
                thread_id,
                len(normalized_attachments),
                ",".join(
                    (
                        f'dataspace://{item["source_id"]}/{item["path"]}'
                        if item["type_code"] == "dataspace"
                        else workspace.to_user_virtual_path(user_id, item["path"])
                    )
                    for item in normalized_attachments
                ),
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

    async def _reply_with_skill_context(self, reference: str, thread_id: str, user_id: str) -> str:
        """Let the planner interpret a skill-provided continuation without owning its policy."""
        events: list[Any] = []
        input_message = {
            "messages": [{
                "role": "user",
                "content": f"以下是工具执行后的参考上下文，请据此继续回复当前请求：\n\n{reference}",
            }]
        }
        async for event in self._require_agent().astream(input_message, config=self._config(thread_id, user_id)):
            events.append(event)
        answer, _ = _extract_final_response(events)
        return answer

    async def run(
        self,
        message: str,
        thread_id: str = "default",
        user_id: str = "default_user",
        attachments: list[Any] | None = None,
        request_id: str | None = None,
        message_id: int | None = None,
    ) -> str:
        request_id = request_id or "-"
        input_message, workspace, before_outputs = self._prepare_request(
            message, thread_id, user_id, request_id, attachments, message_id
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
        execution_spec = _extract_execution_spec(answer)
        if execution_spec is not None:
            log.info(
                "planner skill execution started request_id=%s thread_id=%s skill_name=%s",
                request_id,
                thread_id,
                execution_spec.get("name", "-"),
            )
            try:
                result = await asyncio.to_thread(_generate_planner_skill, execution_spec, thread_id)
            except FileExistsError as exc:
                log.info(
                    "planner skill already exists request_id=%s thread_id=%s path=%s",
                    request_id,
                    thread_id,
                    exc,
                )
                answer = f"{exc}\n如需替换它，请回复“覆盖生成”。"
            except Exception:
                log.exception(
                    "planner skill execution failed request_id=%s thread_id=%s",
                    request_id,
                    thread_id,
                )
                raise
            else:
                followup = _skill_followup_prompt(result)
                if followup:
                    log.info("planner skill requested followup request_id=%s", request_id)
                    answer = await self._reply_with_skill_context(followup, thread_id, user_id)
                    retry_spec = _extract_execution_spec(answer)
                    if retry_spec is not None:
                        result = await asyncio.to_thread(_generate_planner_skill, retry_spec, thread_id)
                        retry_followup = _skill_followup_prompt(result)
                        answer = retry_followup or _format_execution_result(result)
                else:
                    answer = _format_execution_result(result)
                log.info(
                    "planner skill execution finished request_id=%s skill_dir=%s",
                    request_id,
                    result.get("skill_dir", "-"),
                )

        if not answer:
            answer = "未收到可执行的 skill 规格，请重新确认生成请求。"
        # PlannerEngine intentionally does not persist planner chats.
        # save_message(user_id, thread_id, "assistant", answer)
        log.info("planner request finished request_id=%s answer_chars=%s", request_id, len(answer))
        return answer

    async def stream_chat(
        self,
        message: str,
        thread_id: str = "default",
        user_id: str = "default_user",
        attachments: list[Any] | None = None,
        request_id: str | None = None,
        message_id: int | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        request_id = request_id or "-"
        input_message, workspace, before_outputs = self._prepare_request(
            message, thread_id, user_id, request_id, attachments, message_id
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
            if answer_delta and PLANNER_EXECUTE_SPEC_MARKER not in latest_answer:
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

        execution_spec = _extract_execution_spec(latest_answer)
        if execution_spec is not None:
            yield {
                "type": "status",
                "stage": "executing_skill",
                "request_id": request_id,
                "thread_id": thread_id,
                "user_id": user_id,
            }
            try:
                result = await asyncio.to_thread(_generate_planner_skill, execution_spec, thread_id)
            except FileExistsError as exc:
                latest_answer = f"{exc}\n如需替换它，请回复“覆盖生成”。"
            else:
                followup = _skill_followup_prompt(result)
                if followup:
                    yield {
                        "type": "status",
                        "stage": "following_up",
                        "request_id": request_id,
                        "thread_id": thread_id,
                        "user_id": user_id,
                    }
                    latest_answer = await self._reply_with_skill_context(followup, thread_id, user_id)
                    retry_spec = _extract_execution_spec(latest_answer)
                    if retry_spec is not None:
                        result = await asyncio.to_thread(_generate_planner_skill, retry_spec, thread_id)
                        retry_followup = _skill_followup_prompt(result)
                        latest_answer = retry_followup or _format_execution_result(result)
                else:
                    latest_answer = _format_execution_result(result)
        elif not latest_answer:
            latest_answer = "未收到可执行的 skill 规格，请重新确认生成请求。"

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
