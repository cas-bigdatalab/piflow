from __future__ import annotations

from typing import Any

from agents.subagent.skill_creator.prompt import (
    SKILL_CREATOR_ROUTE_MARKER,
    is_skill_creator_route_marker,
)


def build_skill_creator_handoff_message(skill_creator_text: str) -> dict[str, str]:
    return {
        "role": "system",
        "content": (
            "当前父线程可参考的 skill 生成结果如下：\n"
            f"{skill_creator_text}\n\n"
            "skill 生成步骤已经完成。"
            "不要再次输出 skill creator 路由标记。"
            "不要提及 subagent、隐藏路由或内部 handoff 过程。"
            "将这份 skill 草案作为补充参考，并以主 agent 的身份直接回复用户。"
            "重新判断缺失的需求是否已经可以借助该 skill 满足。"
            "如果可以，使用刚生成的 skill 生成或更新相应的 DAG。"
        ),
    }


def resolve_handoff_final_answer(candidate_text: str, fallback_text: str) -> str:
    if is_skill_creator_route_marker(candidate_text):
        return fallback_text
    return candidate_text


def is_skill_creator_route_prefix(candidate_text: str | None) -> bool:
    if candidate_text is None:
        return False

    text = str(candidate_text).strip()
    if not text:
        return False

    return SKILL_CREATOR_ROUTE_MARKER.startswith(text)


def coerce_subagent_event_to_agent_event(
    event: dict[str, Any],
    *,
    preview_text: callable,
) -> dict[str, Any] | None:
    event_type = str(event.get("type") or "")
    task_name = str(event.get("task_name") or "subagent")

    if event_type == "subagent_event":
        nodes = event.get("nodes") if isinstance(event.get("nodes"), list) else []
        tool_calls = event.get("tool_calls") if isinstance(event.get("tool_calls"), list) else []
        preview = event.get("preview")
        return {
            "type": "agent_event",
            "request_id": event.get("request_id"),
            "index": event.get("index"),
            "nodes": [task_name, *nodes] if task_name not in nodes else nodes,
            "message_types": event.get("message_types") if isinstance(event.get("message_types"), list) else [],
            "tool_calls": tool_calls,
            "preview": preview_text(preview or task_name),
        }

    if event_type == "subagent_status":
        stage = str(event.get("stage") or "running")
        return {
            "type": "agent_event",
            "request_id": event.get("request_id"),
            "index": event.get("index"),
            "nodes": [task_name, stage],
            "message_types": [],
            "tool_calls": [],
            "preview": f"{task_name}:{stage}",
        }

    if event_type == "subagent_reasoning_delta":
        return {
            "type": "agent_event",
            "request_id": event.get("request_id"),
            "index": event.get("index"),
            "nodes": [task_name, "reasoning"],
            "message_types": [],
            "tool_calls": [],
            "preview": f"{task_name}:reasoning",
        }

    if event_type == "subagent_message_delta":
        return {
            "type": "agent_event",
            "request_id": event.get("request_id"),
            "index": event.get("index"),
            "nodes": [task_name, "summarizing"],
            "message_types": [],
            "tool_calls": [],
            "preview": f"{task_name}:summarizing",
        }

    return event
