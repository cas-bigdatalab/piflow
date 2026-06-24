from __future__ import annotations

import time
import uuid
from typing import Any, Awaitable, Callable

from agents.subagent.skill_creator.factory import (
    SkillCreatorAgentFactory,
    build_transient_thread_id,
)

SKILL_CREATOR_TASK = "skill_creator"


class SkillCreatorService:
    def __init__(
        self,
        *,
        skill_creator_agent: Any,
        emit_subagent_progress: Callable[..., None],
        spawn_background_subagent: Callable[..., Awaitable[Any]],
        log_stream_event: Callable[[str, int, Any], dict[str, Any]],
        split_stream_part: Callable[[Any], tuple[str | None, Any]],
        is_ai_message: Callable[[Any], bool],
        extract_reasoning_text: Callable[[Any], str],
        merge_text_delta: Callable[[str, str], tuple[str, str]],
        message_content_text: Callable[[Any], str],
        extract_reasoning_from_event: Callable[[Any], str],
        extract_final_response: Callable[[list[Any]], tuple[str, dict[str, Any] | None]],
        preview_text: Callable[[Any], str],
    ) -> None:
        self.skill_creator_agent = skill_creator_agent
        self._emit_subagent_progress = emit_subagent_progress
        self._spawn_background_subagent = spawn_background_subagent
        self._log_stream_event = log_stream_event
        self._split_stream_part = split_stream_part
        self._is_ai_message = is_ai_message
        self._extract_reasoning_text = extract_reasoning_text
        self._merge_text_delta = merge_text_delta
        self._message_content_text = message_content_text
        self._extract_reasoning_from_event = extract_reasoning_from_event
        self._extract_final_response = extract_final_response
        self._preview_text = preview_text

    def build_context(
        self,
        *,
        parent_thread_id: str,
        user_id: str,
        request_id: str,
    ) -> dict[str, str]:
        subagent_thread_id = build_transient_thread_id("skill_creator")
        return {
            "parent_thread_id": parent_thread_id,
            "user_id": user_id,
            "request_id": request_id,
            "fork_reason": "user_requested_skill_creator",
            "context_text": f"Parent thread id: {parent_thread_id}\nSubagent thread id: {subagent_thread_id}",
        }

    def build_subagent_input(self, messages: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "messages": [
                {
                    "role": item.get("role", ""),
                    "content": item.get("content", ""),
                }
                for item in messages
            ],
        }

    async def run(
        self,
        *,
        parent_thread_id: str,
        user_id: str,
        request_id: str,
        messages: list[dict[str, Any]],
        on_event: Callable[[dict[str, Any]], Awaitable[None]] | None = None,
    ) -> tuple[str, dict[str, Any] | None]:
        context = self.build_context(
            parent_thread_id=parent_thread_id,
            user_id=user_id,
            request_id=request_id,
        )
        task_name = SKILL_CREATOR_TASK
        subagent_thread_id = str(context["context_text"]).split("Subagent thread id: ", 1)[1]
        subagent_request_id = f"{request_id}:{uuid.uuid4().hex[:8]}"
        subagent = self.skill_creator_agent or SkillCreatorAgentFactory.create_agent(
            context_text=context["context_text"],
        )
        subagent_input = self.build_subagent_input(messages)
        subagent_config = {
            "configurable": {
                "thread_id": parent_thread_id,
                "user_id": user_id,
            }
        }
        latest_answer = ""
        latest_reasoning = ""
        token_usage = None
        update_events: list[Any] = []
        event_count = 0
        start_stream = time.time()

        async def _emit(event: dict[str, Any]) -> None:
            if on_event is not None:
                await on_event(event)

        self._emit_subagent_progress(
            task_name,
            "preparing",
            trace_id=subagent_request_id,
            parent_thread_id=parent_thread_id,
            subagent_thread_id=subagent_thread_id,
        )
        await _emit(
            {
                "type": "subagent_status",
                "request_id": request_id,
                "task_name": task_name,
                "stage": "preparing",
                "parent_thread_id": parent_thread_id,
                "subagent_thread_id": subagent_thread_id,
            }
        )

        async def _runner() -> tuple[str, dict[str, Any] | None]:
            nonlocal latest_answer, latest_reasoning, token_usage, event_count

            self._emit_subagent_progress(
                task_name,
                "running",
                trace_id=subagent_request_id,
                parent_thread_id=parent_thread_id,
                subagent_thread_id=subagent_thread_id,
            )
            await _emit(
                {
                    "type": "subagent_status",
                    "request_id": request_id,
                    "task_name": task_name,
                    "stage": "running",
                    "parent_thread_id": parent_thread_id,
                    "subagent_thread_id": subagent_thread_id,
                }
            )

            async for stream_part in subagent.astream(
                subagent_input,
                config=subagent_config,
                stream_mode=["messages", "updates"],
            ):
                mode, payload = self._split_stream_part(stream_part)

                if mode == "updates":
                    update_events.append(payload)
                    event_count += 1
                    summary = self._log_stream_event(subagent_request_id, event_count, payload)
                    self._emit_subagent_progress(
                        task_name,
                        "event",
                        trace_id=subagent_request_id,
                        parent_thread_id=parent_thread_id,
                        subagent_thread_id=subagent_thread_id,
                        index=event_count,
                        preview=summary["preview"],
                    )
                    await _emit(
                        {
                            "type": "subagent_event",
                            "request_id": request_id,
                            "task_name": task_name,
                            "index": event_count,
                            "parent_thread_id": parent_thread_id,
                            "subagent_thread_id": subagent_thread_id,
                            "nodes": summary["nodes"],
                            "message_types": summary["message_types"],
                            "tool_calls": summary["tool_calls"],
                            "preview": summary["preview"],
                        }
                    )
                    continue

                if mode != "messages":
                    continue

                if not isinstance(payload, tuple) or len(payload) != 2:
                    continue

                sub_message, metadata = payload
                if not self._is_ai_message(sub_message):
                    continue

                response_metadata = getattr(sub_message, "response_metadata", None) or {}
                current_token_usage = response_metadata.get("token_usage")
                if current_token_usage:
                    token_usage = current_token_usage

                reasoning_piece = self._extract_reasoning_text(sub_message)
                reasoning_delta, latest_reasoning = self._merge_text_delta(
                    latest_reasoning,
                    reasoning_piece,
                )
                if reasoning_delta:
                    self._emit_subagent_progress(
                        task_name,
                        "reasoning",
                        trace_id=subagent_request_id,
                        parent_thread_id=parent_thread_id,
                        subagent_thread_id=subagent_thread_id,
                        preview=self._preview_text(reasoning_delta),
                    )
                    await _emit(
                        {
                            "type": "subagent_reasoning_delta",
                            "request_id": request_id,
                            "task_name": task_name,
                            "delta": reasoning_delta,
                            "content": latest_reasoning,
                            "parent_thread_id": parent_thread_id,
                            "subagent_thread_id": subagent_thread_id,
                            "node": metadata.get("langgraph_node") if isinstance(metadata, dict) else None,
                        }
                    )

                if getattr(sub_message, "tool_call_chunks", None) or getattr(sub_message, "tool_calls", None):
                    continue

                answer_piece = self._message_content_text(getattr(sub_message, "content", ""))
                answer_delta, latest_answer = self._merge_text_delta(latest_answer, answer_piece)
                if answer_delta:
                    self._emit_subagent_progress(
                        task_name,
                        "summarizing",
                        trace_id=subagent_request_id,
                        parent_thread_id=parent_thread_id,
                        subagent_thread_id=subagent_thread_id,
                        preview=self._preview_text(answer_delta),
                    )
                    await _emit(
                        {
                            "type": "subagent_message_delta",
                            "request_id": request_id,
                            "task_name": task_name,
                            "delta": answer_delta,
                            "content": latest_answer,
                            "parent_thread_id": parent_thread_id,
                            "subagent_thread_id": subagent_thread_id,
                            "node": metadata.get("langgraph_node") if isinstance(metadata, dict) else None,
                        }
                    )

            if update_events:
                if not latest_reasoning:
                    latest_reasoning = self._extract_reasoning_from_event(update_events[-1])
                if not latest_answer:
                    latest_answer, update_token_usage = self._extract_final_response(update_events)
                    if update_token_usage and not token_usage:
                        token_usage = update_token_usage

            self._emit_subagent_progress(
                task_name,
                "completed",
                trace_id=subagent_request_id,
                parent_thread_id=parent_thread_id,
                subagent_thread_id=subagent_thread_id,
                answer_chars=len(latest_answer),
            )
            await _emit(
                {
                    "type": "subagent_status",
                    "request_id": request_id,
                    "task_name": task_name,
                    "stage": "completed",
                    "parent_thread_id": parent_thread_id,
                    "subagent_thread_id": subagent_thread_id,
                    "answer_chars": len(latest_answer),
                }
            )
            return latest_answer, token_usage

        task = await self._spawn_background_subagent(
            task_name,
            _runner,
            trace_id=subagent_request_id,
        )
        try:
            return await task
        finally:
            self._emit_subagent_progress(
                task_name,
                "destroyed",
                trace_id=subagent_request_id,
                parent_thread_id=parent_thread_id,
                subagent_thread_id=subagent_thread_id,
            )
            await _emit(
                {
                    "type": "subagent_status",
                    "request_id": request_id,
                    "task_name": task_name,
                    "stage": "destroyed",
                    "parent_thread_id": parent_thread_id,
                    "subagent_thread_id": subagent_thread_id,
                }
            )
