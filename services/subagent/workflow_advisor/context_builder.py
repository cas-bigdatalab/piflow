# runtime/workflow_advisor/context_builder.py

from __future__ import annotations

from typing import Any, Dict, List, Optional

from agents.subagent.workflow_advisor.schema import (
    AdvisorCanvasBinding,
    AdvisorCanvasContext,
    AdvisorCanvasEdge,
    AdvisorCanvasNode,
    AdvisorNodeOutputParam,
    AdvisorNodeParam,
)


# 你自己的 skill 查询函数
# from xxx import get_skill_info_by_id


def infer_node_role(skill_name: Optional[str], node_name: Optional[str]) -> str:
    """
    简单推断节点角色，供模型阅读时参考。
    """
    name = (skill_name or "") + " " + (node_name or "")
    lower = name.lower()

    if "source" in lower or "input" in lower or "输入" in name:
        return "source"
    if "save" in lower or "sink" in lower or "output" in lower or "输出" in name:
        return "sink"
    return "processor"


def build_canvas_summary_text(
        task_name: Optional[str],
        task_description: Optional[str],
        nodes: List[AdvisorCanvasNode],
        edges: List[AdvisorCanvasEdge],
        bindings: List[AdvisorCanvasBinding],
) -> str:
    lines: List[str] = []

    if task_name:
        lines.append(f"任务名称：{task_name}")
    if task_description:
        lines.append(f"任务描述：{task_description}")

    lines.append(f"当前画板共有 {len(nodes)} 个节点，{len(edges)} 条边，{len(bindings)} 条参数绑定。")

    if nodes:
        lines.append("当前节点：")
        for n in nodes:
            skill_part = n.skill_name or n.skill_id or "未知技能"
            zh_part = f"（{n.skill_name_zh}）" if n.skill_name_zh else ""
            lines.append(f"- {n.node_id}: {n.node_name} -> {skill_part}{zh_part}")

    if bindings:
        lines.append("主要参数绑定：")
        for b in bindings[:20]:
            lines.append(
                f"- {b.from_node_id}.{b.from_param_name} -> {b.to_node_id}.{b.to_param_name}"
            )

    return "\n".join(lines)


def summarize_canvas_dsl(
        canvas_dsl: Dict[str, Any],
        *,
        workflow_id: Optional[str] = None,
        selected_node_id: Optional[str] = None,
        skill_resolver=None,
) -> AdvisorCanvasContext:
    """
    将前端DSL转换为适合编排向导理解的上下文。

    skill_resolver: Callable[[skill_id: str], DagSkill | None]
        用于通过 skill_id 查询 DagSkill
    """
    task = canvas_dsl.get("task") or {}
    raw_nodes = canvas_dsl.get("nodes") or []
    raw_edges = canvas_dsl.get("edges") or []
    raw_bindings = canvas_dsl.get("bindings") or []

    nodes: List[AdvisorCanvasNode] = []
    edges: List[AdvisorCanvasEdge] = []
    bindings: List[AdvisorCanvasBinding] = []

    # 1) 解析节点
    for item in raw_nodes:
        skill = item.get("skill") or {}
        skill_id = skill.get("skill_id")
        skill_version = skill.get("version")

        skill_name = None
        skill_name_zh = None
        skill_description = None

        # 默认先用DSL自带的信息（如果以后前端/后端愿意直接补进DSL也兼容）
        skill_name = skill.get("skill_name") or None
        skill_name_zh = skill.get("skill_name_zh") or None
        skill_description = skill.get("description") or None

        # 如果只有 skill_id，则走数据库/注册表查询
        if skill_id and skill_resolver:
            try:
                dag_skill = skill_resolver(skill_id)
                if dag_skill:
                    skill_name = skill_name or dag_skill.skill_name
                    skill_name_zh = skill_name_zh or dag_skill.name_zh
                    skill_description = skill_description or dag_skill.description
            except Exception:
                # 这里建议你打日志，不要中断整体流程
                pass

        input_params = []
        for p in item.get("input_params", []) or []:
            input_params.append(
                AdvisorNodeParam(
                    param_name=p.get("param_name"),
                    value_mode=p.get("value_mode"),
                    param_value=p.get("param_value"),
                    ref_type=p.get("_refType"),
                    binding_id=p.get("binding_id"),
                )
            )

        output_params = []
        for p in item.get("out_params", []) or []:
            output_params.append(
                AdvisorNodeOutputParam(
                    param_name=p.get("param_name"),
                    param_type=p.get("param_type"),
                )
            )

        role = infer_node_role(skill_name, item.get("node_name"))

        nodes.append(
            AdvisorCanvasNode(
                node_id=item.get("node_id"),
                node_name=item.get("node_name"),
                node_type=item.get("node_type"),
                role=role,
                skill_id=skill_id,
                skill_name=skill_name,
                skill_name_zh=skill_name_zh,
                skill_description=skill_description,
                skill_version=skill_version,
                input_params=input_params,
                output_params=output_params,
            )
        )

    # 2) 解析边
    for e in raw_edges:
        edges.append(
            AdvisorCanvasEdge(
                edge_id=e.get("edge_id"),
                from_node_id=e.get("from_node_id"),
                to_node_id=e.get("to_node_id"),
            )
        )

    # 3) 解析参数绑定
    for b in raw_bindings:
        bindings.append(
            AdvisorCanvasBinding(
                binding_id=b.get("binding_id"),
                from_node_id=b.get("from_node_id"),
                from_param_name=b.get("from_param_name"),
                to_node_id=b.get("to_node_id"),
                to_param_name=b.get("to_param_name"),
            )
        )

    summary_text = build_canvas_summary_text(
        task_name=task.get("dag_task_name"),
        task_description=task.get("description"),
        nodes=nodes,
        edges=edges,
        bindings=bindings,
    )

    return AdvisorCanvasContext(
        workflow_id=workflow_id or task.get("dag_task_id"),
        task_name=task.get("dag_task_name"),
        task_description=task.get("description"),
        selected_node_id=selected_node_id,
        nodes=nodes,
        edges=edges,
        bindings=bindings,
        node_count=len(nodes),
        edge_count=len(edges),
        binding_count=len(bindings),
        summary_text=summary_text,
    )