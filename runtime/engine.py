import logging
import time
from typing import Any, AsyncIterator

from agents.factory import AgentFactory
from infra.config_loader import get_settings
from infra.env_loader import load_dotenv_file
from infra.logging import init_logging
from mcp_runtime.mcp_runtime import MCPRuntime
from runtime.chat_store import create_thread, get_messages, init_db, save_message, update_thread_time
from runtime.workspace_manager import WorkspaceManager
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

        messages = []
        for item in history:
            messages.append({
                "role": item["role"],
                "content": item["content"],
            })

        messages.append({
            "role": "user",
            "content": message,
        })

        save_message(user_id, thread_id, "user", message)

        workspace = WorkspaceManager()
        before_outputs = workspace.list_outputs()

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

    async def run(
        self,
        message: str,
        thread_id: str = "default",
        user_id: str = "default_user",
        request_id: str | None = None,
    ):
        start_total = time.time()
        request_id = request_id or "-"
        input_message, workspace, before_outputs = self._prepare_request(
            message,
            thread_id,
            user_id,
            request_id,
        )

        config = {
            "configurable": {
                "thread_id": thread_id,
            }
        }

        events = []
        start_stream = time.time()
        event_count = 0

        try:
            async for event in self.agent.astream(input_message, config=config):
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

        new_files = workspace.detect_new_outputs(before_outputs)
        if new_files:
            events.append({
                "type": "artifact",
                "files": [f"/outputs/{name}" for name in new_files],
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
        request_id: str | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        start_total = time.time()
        request_id = request_id or "-"
        input_message, workspace, before_outputs = self._prepare_request(
            message,
            thread_id,
            user_id,
            request_id,
        )

        config = {
            "configurable": {
                "thread_id": thread_id,
            }
        }

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
        token_usage = None

        try:
            async for event in self.agent.astream(input_message, config=config):
                event_count += 1
                summary = self._log_stream_event(request_id, event_count, event)

                yield {
                    "type": "agent_event",
                    "request_id": request_id,
                    "index": event_count,
                    "nodes": summary["nodes"],
                    "message_types": summary["message_types"],
                    "tool_calls": summary["tool_calls"],
                    "preview": summary["preview"],
                }

                current_answer, current_token_usage = _extract_ai_message_from_event(event)
                if current_token_usage:
                    token_usage = current_token_usage

                if not current_answer:
                    continue

                if current_answer.startswith(latest_answer):
                    delta = current_answer[len(latest_answer):]
                    if delta:
                        yield {
                            "type": "message_delta",
                            "request_id": request_id,
                            "delta": delta,
                            "content": current_answer,
                        }
                elif current_answer != latest_answer:
                    yield {
                        "type": "message",
                        "request_id": request_id,
                        "content": current_answer,
                    }

                latest_answer = current_answer
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

        new_files = workspace.detect_new_outputs(before_outputs)
        if new_files:
            log.info(
                "artifacts detected request_id=%s files=%s",
                request_id,
                ",".join(new_files),
            )
            yield {
                "type": "artifact",
                "request_id": request_id,
                "files": [f"/outputs/{name}" for name in new_files],
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

        async for event in self.agent.astream(input_message, config=config):
            yield event

    async def shutdown(self):
        log.info("shutting down Agent Runtime")
        await self.mcp_runtime.shutdown()
        log.info("shutdown complete")
