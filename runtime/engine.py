import asyncio
import logging
import time
from typing import Any, AsyncIterator, Awaitable, Callable

from agents.factory import AgentFactory
from infra.config_loader import get_settings
from infra.env_loader import load_dotenv_file
from infra.logging import init_logging
from mcp_runtime.mcp_runtime import MCPRuntime
from runtime.chat_store import create_thread, get_messages, save_message, update_thread_time, init_db
from runtime.dag_manager import init_dag_db
from runtime.piflow_adapter import init_piflow_run_tracking_db
from runtime.skill_manage import init_dag_skills_to_database
from runtime.workspace_manager import WorkspaceManager
from runtime.events import (
    emit_subagent_finished,
    emit_subagent_progress as emit_subagent_progress_event,
    emit_subagent_started,
)
from services.user_service import init_default_user
from tools.core.registry import registry

log = logging.getLogger("flow.engine")


def _preview_text(value: Any, limit: int = 120) -> str:
    if value is None:
        return ""

    text = str(value).replace("\r", " ").replace("\n", " ").strip()
    if len(text) <= limit:
        return text
    return text[:limit] + "..."


def _message_content_text(content: Any) -> str:
    if content is None:
        return ""

    if isinstance(content, str):
        return content

    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict):
                text = item.get("text") or item.get("content") or item.get("input")
                if text:
                    parts.append(str(text))
            elif item is not None:
                parts.append(str(item))
        return "".join(parts)

    if isinstance(content, dict):
        text = content.get("text") or content.get("content") or content.get("input")
        if text:
            return str(text)

    return str(content)


def _message_content_preview(content: Any) -> str:
    return _preview_text(_message_content_text(content))


def _build_attachment_context(attachments: list[str] | None) -> str:
    valid = []
    for item in attachments or []:
        if not isinstance(item, str):
            continue
        path = item.strip()
        if path:
            valid.append(path)

    if not valid:
        return ""

    lines = [
        "Uploaded files for this request:",
        "Use these files as the primary inputs for the current task.",
        "Do not scan the whole workspace or ask which file to use unless the request is truly ambiguous.",
    ]
    lines.extend(f"- {path}" for path in valid)
    if len(valid) == 1:
        lines.append(f'If the user says "this file", "that file", or "uploaded file", resolve it to: {valid[0]}')
    else:
        lines.append("If the user refers to an uploaded file, resolve it from the list above before asking a follow-up question.")
    return "\n".join(lines)

def _append_reasoning_part(parts: list[str], seen: set[str], value: Any) -> None:
    text = _message_content_text(value).strip()
    if not text or text in seen:
        return
    seen.add(text)
    parts.append(text)


def _extract_reasoning_text(message: Any) -> str:
    parts: list[str] = []
    seen: set[str] = set()

    additional_kwargs = getattr(message, "additional_kwargs", None) or {}
    reasoning = additional_kwargs.get("reasoning")

    if isinstance(reasoning, str):
        _append_reasoning_part(parts, seen, reasoning)
    elif isinstance(reasoning, dict):
        _append_reasoning_part(parts, seen, reasoning.get("reasoning") or reasoning.get("text"))
        for item in reasoning.get("summary") or []:
            if isinstance(item, dict):
                _append_reasoning_part(parts, seen, item.get("text") or item.get("reasoning"))
            else:
                _append_reasoning_part(parts, seen, item)
    elif isinstance(reasoning, list):
        for item in reasoning:
            if isinstance(item, dict):
                _append_reasoning_part(parts, seen, item.get("reasoning") or item.get("text"))
                for summary_item in item.get("summary") or []:
                    if isinstance(summary_item, dict):
                        _append_reasoning_part(
                            parts,
                            seen,
                            summary_item.get("text") or summary_item.get("reasoning"),
                        )
                    else:
                        _append_reasoning_part(parts, seen, summary_item)
            else:
                _append_reasoning_part(parts, seen, item)

    content = getattr(message, "content", None)
    if isinstance(content, list):
        for block in content:
            if not isinstance(block, dict) or block.get("type") != "reasoning":
                continue
            _append_reasoning_part(parts, seen, block.get("reasoning") or block.get("text"))
            for item in block.get("summary") or []:
                if isinstance(item, dict):
                    _append_reasoning_part(parts, seen, item.get("text") or item.get("reasoning"))
                else:
                    _append_reasoning_part(parts, seen, item)

    return "\n".join(parts).strip()


def _is_ai_message(message: Any) -> bool:
    message_type = str(getattr(message, "type", message.__class__.__name__)).lower()
    return "ai" in message_type


def _extract_ai_message_from_event(event: Any) -> tuple[str, dict[str, Any] | None]:
    if not isinstance(event, dict):
        return "", None

    for payload in event.values():
        if not isinstance(payload, dict):
            continue

        messages = payload.get("messages")
        if not isinstance(messages, list):
            continue

        for message in reversed(messages):
            if not _is_ai_message(message):
                continue

            tool_calls = getattr(message, "tool_calls", None)
            if tool_calls:
                continue

            text = _message_content_text(getattr(message, "content", ""))
            metadata = getattr(message, "response_metadata", None)
            token_usage = metadata.get("token_usage") if metadata else None
            return text, token_usage

    return "", None


def _extract_final_response(events: list[Any]) -> tuple[str, dict[str, Any] | None]:
    for event in reversed(events):
        text, token_usage = _extract_ai_message_from_event(event)
        if text or token_usage:
            return text, token_usage
    return "", None


def _extract_reasoning_from_event(event: Any) -> str:
    if not isinstance(event, dict):
        return ""

    parts: list[str] = []
    seen: set[str] = set()

    for payload in event.values():
        if not isinstance(payload, dict):
            continue

        messages = payload.get("messages")
        if not isinstance(messages, list):
            continue

        for message in messages:
            if not _is_ai_message(message):
                continue
            _append_reasoning_part(parts, seen, _extract_reasoning_text(message))

    return "\n".join(parts).strip()


def _split_stream_part(stream_part: Any) -> tuple[str | None, Any]:
    if not isinstance(stream_part, tuple):
        return None, stream_part

    if len(stream_part) == 2:
        mode, data = stream_part
        return str(mode), data

    if len(stream_part) == 3:
        _, mode, data = stream_part
        return str(mode), data

    return None, stream_part


def _merge_text_delta(current_text: str, incoming_text: str) -> tuple[str, str]:
    if not incoming_text:
        return "", current_text

    if incoming_text.startswith(current_text):
        delta = incoming_text[len(current_text):]
        return delta, incoming_text

    return incoming_text, current_text + incoming_text


def _summarize_event(event: Any) -> dict[str, Any]:
    if not isinstance(event, dict):
        return {
            "nodes": ["unknown"],
            "message_types": [],
            "tool_calls": [],
            "preview": _preview_text(event),
        }

    nodes: list[str] = []
    message_types: list[str] = []
    tool_calls: list[str] = []
    preview = ""

    for node_name, payload in event.items():
        nodes.append(str(node_name))

        if not isinstance(payload, dict):
            if not preview:
                preview = _preview_text(payload)
            continue

        messages = payload.get("messages")
        if not isinstance(messages, list):
            continue

        for message in messages:
            message_type = getattr(message, "type", None) or message.__class__.__name__
            message_types.append(str(message_type))

            for tool_call in getattr(message, "tool_calls", None) or []:
                if isinstance(tool_call, dict):
                    name = tool_call.get("name") or tool_call.get("id")
                else:
                    name = getattr(tool_call, "name", None) or getattr(tool_call, "id", None)

                if name:
                    tool_calls.append(str(name))

            if not preview and _is_ai_message(message) and not getattr(message, "tool_calls", None):
                preview = _message_content_preview(getattr(message, "content", ""))

    return {
        "nodes": nodes,
        "message_types": message_types,
        "tool_calls": tool_calls,
        "preview": preview,
    }


class AgentEngine:

    def __init__(self, agent=None):
        self.agent = agent
        self.initialized = False
        self.settings = get_settings()
        self.mcp_runtime = MCPRuntime(self.settings.mcp)

    async def initialize(self):
        if self.initialized:
            return

        init_logging()
        log.info("initializing Agent Runtime")

        load_dotenv_file()
        log.info("loading env files complete")

        init_db()
        init_dag_db()
        init_piflow_run_tracking_db()
        init_dag_skills_to_database()
        init_default_user()
        log.info("initializing database complete")

        self.agent = AgentFactory.create_agent()

        self.initialized = True
        log.info("Agent Runtime initialized")

    def _prepare_request(
        self,
        message: str,
        thread_id: str,
        user_id: str,
        request_id: str,
        attachments: list[str] | None = None,
        message_id: int | None = None,
    ) -> tuple[dict[str, Any], WorkspaceManager, list[str]]:
        registry.begin_request()

        log.info(
            "request started request_id=%s thread_id=%s user_id=%s input_chars=%s preview=%s",
            request_id,
            thread_id,
            user_id,
            len(message),
            _preview_text(message),
        )

        history = get_messages(thread_id)
        log.info(
            "history loaded request_id=%s thread_id=%s message_count=%s",
            request_id,
            thread_id,
            len(history),
        )

        if not history:
            create_thread(user_id, thread_id, message[:30])

        update_thread_time(thread_id)

        attachment_context = _build_attachment_context(attachments)
        input_content = message
        if attachment_context:
            input_content = f"{message}\n\n{attachment_context}"
            log.info(
                "attachments injected request_id=%s thread_id=%s attachment_count=%s attachments=%s",
                request_id,
                thread_id,
                len(attachments or []),
                ",".join(attachments or []),
            )

        messages = []
        injected = False
        for item in history:
            content = item["content"]
            if message_id is not None and item.get("id") == message_id:
                content = input_content
                injected = True

            messages.append({
                "role": item["role"],
                "content": content,
            })

        if not injected:
            messages.append({
                "role": "user",
                "content": input_content,
            })
            save_message(user_id, thread_id, "user", message)

        workspace = WorkspaceManager()
        before_outputs = workspace.snapshot_downloadables()

        return {
            "messages": messages,
        }, workspace, before_outputs

    def _log_stream_event(self, request_id: str, event_count: int, event: Any) -> dict[str, Any]:
        summary = _summarize_event(event)
        log.info(
            "agent event request_id=%s index=%s nodes=%s message_types=%s tool_calls=%s preview=%s",
            request_id,
            event_count,
            ",".join(summary["nodes"]) or "-",
            ",".join(summary["message_types"]) or "-",
            ",".join(summary["tool_calls"]) or "-",
            summary["preview"] or "-",
        )
        return summary

    def _log_request_finish(
        self,
        request_id: str,
        final_answer: str,
        token_usage: dict[str, Any] | None,
        latency: float,
    ) -> None:
        log.info(
            "request finished request_id=%s total_cost=%.2fs answer_chars=%s",
            request_id,
            latency,
            len(final_answer),
        )

        if token_usage:
            log.info(
                "llm_usage request_id=%s latency=%.2fs input_tokens=%s output_tokens=%s total_tokens=%s",
                request_id,
                latency,
                token_usage.get("prompt_tokens"),
                token_usage.get("completion_tokens"),
                token_usage.get("total_tokens"),
            )
        else:
            log.info(
                "llm_usage request_id=%s latency=%.2fs token_usage=unknown",
                request_id,
                latency,
            )

    def build_subagent_context(
        self,
        parent_thread_id: str,
        user_id: str,
        request_id: str,
        fork_reason: str | None = None,
        context_text: str | None = None,
    ) -> dict[str, Any]:
        return {
            "parent_thread_id": parent_thread_id,
            "user_id": user_id,
            "request_id": request_id,
            "fork_reason": fork_reason,
            "context_text": context_text,
        }

    async def spawn_background_subagent(
        self,
        task_name: str,
        runner: Callable[[], Awaitable[Any]],
        trace_id: str | None = None,
    ) -> asyncio.Task[Any]:
        async def _wrapped():
            emit_subagent_started({"task_name": task_name}, trace_id=trace_id)
            try:
                result = await runner()
                emit_subagent_finished(
                    {
                        "task_name": task_name,
                        "success": True,
                    },
                    trace_id=trace_id,
                )
                return result
            except Exception as exc:
                emit_subagent_finished(
                    {
                        "task_name": task_name,
                        "success": False,
                        "error": str(exc),
                    },
                    trace_id=trace_id,
                )
                raise

        task = asyncio.create_task(_wrapped(), name=task_name)
        return task

    def emit_subagent_progress(
        self,
        task_name: str,
        stage: str,
        trace_id: str | None = None,
        **payload: Any,
    ) -> None:
        emit_subagent_progress_event(
            {
                "task_name": task_name,
                "stage": stage,
                **payload,
            },
            trace_id=trace_id,
        )

    async def run(
        self,
        message: str,
        thread_id: str = "default",
        user_id: str = "default_user",
        attachments: list[str] | None = None,
        request_id: str | None = None,
        message_id: int | None = None,
    ):
        start_total = time.time()
        request_id = request_id or "-"
        input_message, workspace, before_outputs = self._prepare_request(
            message,
            thread_id,
            user_id,
            request_id,
            attachments,
            message_id,
        )

        config = {
            "configurable": {
                "thread_id": thread_id,
                "user_id": user_id,
            }
        }

        agent = self.agent
        assert agent is not None

        events = []
        start_stream = time.time()
        event_count = 0

        try:
            async for event in agent.astream(input_message, config=config):
                events.append(event)
                event_count += 1
                self._log_stream_event(request_id, event_count, event)
        except Exception:
            log.exception(
                "agent stream failed request_id=%s thread_id=%s user_id=%s",
                request_id,
                thread_id,
                user_id,
            )
            raise

        log.info(
            "agent stream finished request_id=%s cost=%.2fs event_count=%s",
            request_id,
            time.time() - start_stream,
            event_count,
        )

        new_files = workspace.detect_changed_downloadables(before_outputs)
        if new_files:
            events.append({
                "type": "artifact",
                "files": new_files,
            })
            log.info(
                "artifacts detected request_id=%s files=%s",
                request_id,
                ",".join(new_files),
            )

        final_answer, token_usage = _extract_final_response(events)
        save_message(user_id, thread_id, "assistant", final_answer)

        latency = time.time() - start_total
        self._log_request_finish(request_id, final_answer, token_usage, latency)
        return final_answer

    async def stream_chat(
        self,
        message: str,
        thread_id: str = "default",
        user_id: str = "default_user",
        attachments: list[str] | None = None,
        request_id: str | None = None,
        message_id: int | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        start_total = time.time()
        request_id = request_id or "-"
        input_message, workspace, before_outputs = self._prepare_request(
            message,
            thread_id,
            user_id,
            request_id,
            attachments,
            message_id,
        )

        config = {
            "configurable": {
                "thread_id": thread_id,
                "user_id": user_id,
            }
        }

        agent = self.agent
        assert agent is not None

        yield {
            "type": "status",
            "stage": "started",
            "request_id": request_id,
            "thread_id": thread_id,
            "user_id": user_id,
        }

        start_stream = time.time()
        event_count = 0
        latest_answer = ""
        latest_reasoning = ""
        token_usage = None
        update_events: list[Any] = []

        try:
            async for stream_part in agent.astream(
                input_message,
                config=config,
                stream_mode=["messages", "updates"],
            ):
                mode, payload = _split_stream_part(stream_part)

                if mode == "updates":
                    update_events.append(payload)
                    event_count += 1
                    summary = self._log_stream_event(request_id, event_count, payload)

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

                if mode != "messages":
                    continue

                if (
                    not isinstance(payload, tuple)
                    or len(payload) != 2
                ):
                    continue

                message, metadata = payload
                if not _is_ai_message(message):
                    continue

                response_metadata = getattr(message, "response_metadata", None) or {}
                current_token_usage = response_metadata.get("token_usage")
                if current_token_usage:
                    token_usage = current_token_usage

                reasoning_piece = _extract_reasoning_text(message)
                reasoning_delta, latest_reasoning = _merge_text_delta(
                    latest_reasoning,
                    reasoning_piece,
                )
                if reasoning_delta:
                    yield {
                        "type": "reasoning_delta",
                        "request_id": request_id,
                        "delta": reasoning_delta,
                        "content": latest_reasoning,
                        "node": metadata.get("langgraph_node") if isinstance(metadata, dict) else None,
                    }

                if getattr(message, "tool_call_chunks", None) or getattr(message, "tool_calls", None):
                    continue

                answer_piece = _message_content_text(getattr(message, "content", ""))
                answer_delta, latest_answer = _merge_text_delta(latest_answer, answer_piece)
                if answer_delta:
                    yield {
                        "type": "message_delta",
                        "request_id": request_id,
                        "delta": answer_delta,
                        "content": latest_answer,
                        "node": metadata.get("langgraph_node") if isinstance(metadata, dict) else None,
                    }
        except Exception:
            log.exception(
                "agent stream failed request_id=%s thread_id=%s user_id=%s",
                request_id,
                thread_id,
                user_id,
            )
            raise

        log.info(
            "agent stream finished request_id=%s cost=%.2fs event_count=%s",
            request_id,
            time.time() - start_stream,
            event_count,
        )

        if update_events:
            if not latest_reasoning:
                latest_reasoning = _extract_reasoning_from_event(update_events[-1])
            if not latest_answer:
                latest_answer, update_token_usage = _extract_final_response(update_events)
                if update_token_usage and not token_usage:
                    token_usage = update_token_usage

        new_files = workspace.detect_changed_downloadables(before_outputs)
        if new_files:
            log.info(
                "artifacts detected request_id=%s files=%s",
                request_id,
                ",".join(new_files),
            )
            yield {
                "type": "artifact",
                "request_id": request_id,
                "files": new_files,
            }

        save_message(user_id, thread_id, "assistant", latest_answer)

        latency = time.time() - start_total
        self._log_request_finish(request_id, latest_answer, token_usage, latency)

        yield {
            "type": "done",
            "request_id": request_id,
            "content": latest_answer,
            "token_usage": token_usage,
            "latency_sec": round(latency, 3),
        }

    async def stream(self, message: str, thread_id: str = "default"):
        registry.begin_request()

        config = {
            "configurable": {
                "thread_id": thread_id
            }
        }

        input_message = {
            "messages": [
                {
                    "role": "user",
                    "content": message
                }
            ]
        }

        agent = self.agent
        assert agent is not None

        async for event in agent.astream(input_message, config=config):
            yield event

    async def shutdown(self):
        log.info("shutting down Agent Runtime")
        await self.mcp_runtime.shutdown()
        log.info("shutdown complete")
