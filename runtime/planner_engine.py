import logging
import time
from typing import Any, AsyncIterator

from agents.skill_planner.factory import SkillPlannerAgentFactory
from runtime.engine import (
    _extract_final_response,
    _extract_reasoning_text,
    _is_ai_message,
    _merge_text_delta,
    _message_content_text,
    _split_stream_part,
    _summarize_event,
)


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

    def _input(self, message: str) -> dict[str, list[dict[str, str]]]:
        return {"messages": [{"role": "user", "content": message}]}

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
        request_id: str | None = None,
    ) -> str:
        request_id = request_id or "-"
        events: list[Any] = []
        agent = self._require_agent()

        log.info("planner request started request_id=%s thread_id=%s user_id=%s", request_id, thread_id, user_id)
        async for event in agent.astream(self._input(message), config=self._config(thread_id, user_id)):
            events.append(event)

        answer, _ = _extract_final_response(events)
        log.info("planner request finished request_id=%s answer_chars=%s", request_id, len(answer))
        return answer

    async def stream_chat(
        self,
        message: str,
        thread_id: str = "default",
        user_id: str = "default_user",
        request_id: str | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        request_id = request_id or "-"
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
            self._input(message),
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
