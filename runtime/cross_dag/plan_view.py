"""把内部的 CrossDagPlan 投影成前端渲染需要的最小结构。

CrossDagPlan 是给引擎和排障用的完整对象：嵌套 DSL、副本打分表、段图、意图原文
一应俱全。前端渲染方案卡片只用得上其中一小部分，其余要么是给执行引擎的
（nested_dsl），要么是同一份信息的第二次出现（intent 里的副本清单和
binding 里的打分表重复），直接整个吐给前端只会让人找不到北。

这里按「界面上要显示什么」来组织，而不是按内部流水线的阶段来组织。
需要完整数据时传 detail=True，排障和引擎自检走那条。
"""

from __future__ import annotations

from typing import Any

from .config import CrossDcConfig, get_cross_dc_config, resolve_cross_dc_config
from .schema import MODE_COMPOSITION, MODE_DIRECT, MODE_UNAVAILABLE, CrossDagPlan


def build_plan_view(
    plan: CrossDagPlan,
    *,
    detail: bool = False,
    config: CrossDcConfig | None = None,
) -> dict[str, Any]:
    if config is not None:
        resolved = config
    else:
        from .registry_stub import get_registry

        resolved = resolve_cross_dc_config(get_cross_dc_config(), get_registry())

    view: dict[str, Any] = {
        "plan_id": plan.plan_id,
        "mode": plan.mode,
        "conclusion": plan.satisfaction.reason if plan.satisfaction else "",
        "validation": plan.validation.to_json(),
        "requirement": _requirement(plan),
    }

    if plan.satisfaction is not None:
        view["coverage"] = _coverage(plan)

    if plan.mode == MODE_DIRECT:
        view["access"] = _access(plan)
    elif plan.mode == MODE_COMPOSITION:
        view["dag"] = _dag(plan, resolved)
        view["sources"] = _sources(plan)
    elif plan.mode == MODE_UNAVAILABLE:
        view["unavailable"] = _unavailable(plan)

    if detail:
        view["detail"] = _detail(plan)
    return view


def stage_brief(stage: str, payload: dict[str, Any]) -> dict[str, Any]:
    """把内部阶段事件压成前端步骤条要的一行摘要。

    内部事件带的是全量（意图原文、打分表、整个嵌套 DSL），排障时有用，推给
    浏览器就是几万字符的噪音 —— 步骤条上只显示一行字。完整结果在最后的
    done 事件里一次给到。
    """
    brief: dict[str, Any] = {"stage": stage, "status": payload.get("status", "")}
    if payload.get("status") != "finished":
        return brief

    summary = ""
    if stage == "intent":
        intent = payload.get("intent") or {}
        summary = (
            f"识别出 {len(intent.get('requirements') or [])} 项需求条件"
            f" · 命中 {len(intent.get('datasets') or [])} 个数据集"
        )
    elif stage in ("satisfaction", "unavailable"):
        summary = str(payload.get("reason") or "")
        brief["mode"] = payload.get("mode", stage)
    elif stage == "access":
        summary = f"目标 {payload.get('dataset_id', '')} · 副本 {payload.get('replica', '')}"
    elif stage == "planning":
        nodes = (payload.get("planning_json") or {}).get("nodes") or []
        summary = f"规划出 {len(nodes)} 个算子"
    elif stage == "expand":
        summary = (
            f"{payload.get('node_count', 0)} 个节点 · "
            f"{payload.get('binding_count', 0)} 条连线"
        )
    elif stage == "bind":
        centers = set((payload.get("center_of") or {}).values())
        summary = f"绑定到 {len(centers)} 个数据节点"
    elif stage == "segment":
        summary = (
            f"{payload.get('segment_count', 0)} 个执行单元 · "
            f"{payload.get('cross_edge_count', 0)} 条跨单元边"
        )
    elif stage == "nest":
        summary = f"嵌套 {payload.get('depth', 1)} 层"
    elif stage == "validate":
        report = payload.get("report") or {}
        errors = report.get("errors") or []
        summary = "校验通过" if not errors else f"{len(errors)} 项校验未通过"

    brief["summary"] = summary
    return brief


def _requirement(plan: CrossDagPlan) -> dict[str, Any]:
    """需求理解。原始意图里那一大坨副本清单不进来 —— 那是绑定阶段的事。"""
    intent = plan.intent
    return {
        "goal": intent.goal,
        "user_request": intent.user_request,
        "facets": [
            {"key": f.key, "label": f.label or f.key, "values": list(f.values)}
            for f in intent.requirements
        ],
        "operations": [
            str(op.get("op") or "").strip()
            for op in intent.operations
            if isinstance(op, dict) and str(op.get("op") or "").strip()
        ],
        "assumptions": list(intent.assumptions),
        "unresolved": list(intent.unresolved),
    }


def _coverage(plan: CrossDagPlan) -> dict[str, Any]:
    """覆盖矩阵。

    需求取值只在 facets 里出现一次，每行的格子按同样顺序排列，前端按下标对齐，
    不用每行再重复一遍需求。格子按缺省编码：能覆盖就只有 {"ok": true}，
    覆盖不了才带上差在哪、是不是压根没声明这个维度。
    """
    report = plan.satisfaction
    assert report is not None
    order = [f.key for f in report.facets]

    datasets = []
    for cover in report.coverages:
        by_key = {c.key: c for c in cover.facets}
        cells = []
        for key in order:
            cell = by_key.get(key)
            if cell is None:
                continue
            item: dict[str, Any] = {"ok": cell.satisfied}
            if not cell.satisfied:
                item["missing"] = list(cell.missing)
                if not cell.declared:
                    # 没声明和声明了但对不上要区分：前者是元数据缺口，
                    # 后者才是真的没有这份数据。
                    item["declared"] = False
            cells.append(item)
        datasets.append(
            {
                "dataset_id": cover.dataset_id,
                "name": cover.name,
                "selected": cover.selected,
                "full_match": cover.full_match,
                "cells": cells,
            }
        )

    return {
        "facets": [
            {"key": f.key, "label": f.label or f.key, "values": list(f.values)}
            for f in report.facets
        ],
        "datasets": datasets,
        "full_match_count": len(report.full_matches),
        "scanned_count": report.scanned_count,
    }


def _access(plan: CrossDagPlan) -> dict[str, Any]:
    """直接获取：目标数据集 + 选中的那个副本。完整打分表在 detail 里。"""
    access = plan.direct_access
    if access is None:
        return {}
    decision = access.replica_decision
    chosen = decision.chosen if decision else None
    return {
        "dataset_id": access.dataset_id,
        "name": access.name,
        "replica": (
            {
                "replica_id": chosen.replica_id,
                "center_id": chosen.center_id,
                "locator": chosen.locator,
                "reason": decision.reason if decision else "",
                "rejected_count": len(decision.rejects) if decision else 0,
            }
            if chosen
            else None
        ),
        "alternatives": [
            {
                "dataset_id": item.get("dataset_id"),
                "name": item.get("name"),
                "selected": item.get("selected"),
            }
            for item in access.alternatives
        ],
    }


def _dag(plan: CrossDagPlan, config: CrossDcConfig) -> dict[str, Any]:
    """要画的是算子级平铺图：节点 + 连线 + 每个节点在哪执行。

    嵌套 DSL 不进来 —— 那是交给执行引擎的结构，界面上没有任何地方展示它，
    却占了整个响应的三分之一。
    """
    dag = plan.logical_dag
    center_of = plan.bind_result.center_of

    def center_name(center_id: str) -> str:
        center = config.centers.get(center_id)
        return center.center_name if center else center_id

    nodes = [
        {
            "id": node.node_id,
            "name": node.node_name,
            "skill_name": node.skill_name or node.skill_id,
            "center_id": center_of.get(node.node_id, ""),
            "center_name": center_name(center_of.get(node.node_id, "")),
        }
        for node in dag.nodes
    ]

    edges = []
    transfers = 0
    for binding in dag.bindings:
        cross = center_of.get(binding.from_node_id) != center_of.get(binding.to_node_id)
        if cross:
            transfers += 1
        edges.append(
            {
                "from": binding.from_node_id,
                "to": binding.to_node_id,
                "cross_center": cross,
            }
        )

    used = [c for c in dict.fromkeys(center_of.values()) if c]
    roots = plan.segment_graph.root_segments()
    return {
        "task_name": dag.task_name,
        "description": dag.description,
        "nodes": nodes,
        "edges": edges,
        "centers": [
            {
                "center_id": center_id,
                "center_name": center_name(center_id),
                "node_count": sum(1 for v in center_of.values() if v == center_id),
            }
            for center_id in used
        ],
        # 跨中心传输次数 == 会生成几个远程子 DAG，这是「智能」值多少钱的直接指标
        "cross_center_transfers": transfers,
        "merge_center_id": (
            plan.segment_graph.segments[roots[0]].center_id if len(roots) == 1 else ""
        ),
        "execution_center_id": plan.execution_center_id,
    }


def _sources(plan: CrossDagPlan) -> list[dict[str, Any]]:
    """组装用到的数据集，以及各自选中的副本。一条一行，够方案卡片渲染。"""
    chosen_of = {
        decision.dataset_id: decision
        for decision in plan.bind_result.replica_decisions
    }
    sources = []
    for dataset in plan.intent.datasets:
        decision = chosen_of.get(dataset.dataset_id)
        chosen = decision.chosen if decision else None
        sources.append(
            {
                "dataset_id": dataset.dataset_id,
                "name": dataset.name,
                "replica_id": chosen.replica_id if chosen else "",
                "center_id": chosen.center_id if chosen else dataset.center_id,
                "reason": decision.reason if decision else "",
            }
        )
    return sources


def _unavailable(plan: CrossDagPlan) -> dict[str, Any]:
    report = plan.satisfaction
    return {
        "missing_values": report.missing_values if report else [],
        "scanned_count": report.scanned_count if report else 0,
        "unresolved": list(plan.intent.unresolved),
    }


def _detail(plan: CrossDagPlan) -> dict[str, Any]:
    """排障与引擎对接用的完整数据。默认不返回。"""
    return {
        "intent": plan.intent.to_json(),
        "binding": {
            "center_of": dict(plan.bind_result.center_of),
            "reasons": dict(plan.bind_result.reasons),
            "replica_decisions": [
                d.to_json() for d in plan.bind_result.replica_decisions
            ],
        },
        "segments": plan.segment_graph.to_json(),
        "logical_dag": plan.logical_dag.to_json(),
        "nested_dsl": plan.nested_dsl,
    }
