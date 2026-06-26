from __future__ import annotations

from typing import Any

from agents.subagent.skill_creator.prompt import (
    SKILL_CREATOR_ROUTE_MARKER,
    is_skill_creator_route_marker,
    strip_route_marker,
)


def build_skill_creator_handoff_message(skill_creator_text: str) -> dict[str, str]:
    return {
        "role": "system",
        "content": (
            "当前父线程可参考的 skill 创建收集结果如下：\n"
            f"{skill_creator_text}\n\n"
            "spec 收集阶段已经完成。现在你必须根据收集结果实际创建 skill 文件，步骤为：\n"
            "1. 在 workspace/skills/generated/<skill_name>/ 下创建 SKILL.md（含 yaml 元数据）\n"
            "2. 在相同目录下创建 skill.json\n"
            "3. 如有脚本则在 scripts/ 下创建对应的脚本文件\n"
            "4. 所有参数名必须与收集结果中确认的名称一致\n"
            "只有文件创建完成后，这个 skill 才能用于 DAG。\n"
            "不要再次输出 skill creator 路由标记。"
            "不要提及 subagent、隐藏路由或内部 handoff 过程。"
            "如果关键信息仍然缺失，继续向用户追问或明确说明当前还不能创建 skill。"
            "**当生成的skill满足了缺失的需求，询问用户是否生成DAG，只有用户明确同意后，才直接输出DAG，切记只能生成DAG，不要输出其他内容。**"
        ),
    }


def resolve_handoff_final_answer(candidate_text: str, fallback_text: str) -> str:
    if is_skill_creator_route_marker(candidate_text):
        return fallback_text
    # 兜底：即使检测失败，也确保标记不会泄露到用户
    sanitized = strip_route_marker(candidate_text)
    return sanitized if sanitized else fallback_text


def is_skill_creator_route_prefix(candidate_text: str | None) -> bool:
    if candidate_text is None:
        return False

    text = str(candidate_text).strip()
    if not text:
        return False

    # 如果标记已完整出现在文本中，视为路由前缀（兼容文本+标记混排）
    if SKILL_CREATOR_ROUTE_MARKER in text:
        return True

    # 流式场景：检查当前累积文本是否以标记的前缀结尾
    for i in range(1, len(SKILL_CREATOR_ROUTE_MARKER)):
        if text.endswith(SKILL_CREATOR_ROUTE_MARKER[:i]):
            return True

    return False


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
