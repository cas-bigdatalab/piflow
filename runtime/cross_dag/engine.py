"""跨域规划流水线编排。"""

from __future__ import annotations

import logging
import uuid
from typing import Any, AsyncIterator, Callable

from .binder import bind_centers
from .config import CrossDcConfig, get_cross_dc_config
from .intent import plan_global_dag, recognize_intent
from .nester import build_nested_dsl
from .planner_bridge import (
    database_param_resolver,
    database_skill_resolver,
    expand_planning_json,
)
from .registry_stub import DatasourceRegistry, get_registry
from .schema import CrossDagError, CrossDagPlan, IntentSpec, LogicalDag, ValidationReport
from .segmenter import build_segment_graph
from .validator import (
    validate_intent_coverage,
    validate_location_hints,
    validate_logical_dag,
    validate_nested_dsl,
    validate_segmentation,
)

log = logging.getLogger("flow.cross_dag.engine")

StageHook = Callable[[str, dict[str, Any]], None]


def plan_cross_dag(
    user_request: str,
    *,
    plan_id: str | None = None,
    llm: Any = None,
    registry: DatasourceRegistry | None = None,
    config: CrossDcConfig | None = None,
    skill_resolver: Callable[[str], str] | None = None,
    on_stage: StageHook | None = None,
    intent: IntentSpec | None = None,
    planning_json: dict[str, Any] | None = None,
) -> CrossDagPlan:
    """完整规划。"""
    resolved_plan_id = plan_id or f"xdc-{uuid.uuid4().hex[:12]}"
    resolved_config = config or get_cross_dc_config()
    resolved_registry = registry or get_registry()
    emit = on_stage or (lambda stage, payload: None)

    emit("intent", {"status": "started"})
    resolved_intent = intent or recognize_intent(
        user_request, llm=llm, registry=resolved_registry
    )
    emit("intent", {"status": "finished", "intent": resolved_intent.to_json()})

    emit("planning", {"status": "started"})
    resolved_planning = planning_json or plan_global_dag(resolved_intent, llm=llm)
    emit("planning", {"status": "finished", "planning_json": resolved_planning})

    emit("expand", {"status": "started"})
    logical_dag = expand_planning_json(
        resolved_planning,
        skill_resolver=skill_resolver or database_skill_resolver(),
        param_resolver=database_param_resolver(),
        task_id=resolved_plan_id,
    )
    logical_report = validate_logical_dag(logical_dag)
    if not logical_report.ok:
        raise CrossDagError("逻辑 DAG 校验失败:\n" + "\n".join(logical_report.errors))
    logical_report.merge(validate_intent_coverage(resolved_intent, logical_dag))
    emit(
        "expand",
        {
            "status": "finished",
            "node_count": len(logical_dag.nodes),
            "binding_count": len(logical_dag.bindings),
            "未被使用的数据集": list(logical_report.warnings),
            "logical_dag": logical_dag.to_json(),
        },
    )

    plan = compile_cross_dag(
        logical_dag,
        intent=resolved_intent,
        plan_id=resolved_plan_id,
        config=resolved_config,
        on_stage=emit,
    )
    plan.validation.merge(logical_report)
    return plan


def compile_cross_dag(
    logical_dag: LogicalDag,
    *,
    intent: IntentSpec,
    plan_id: str,
    config: CrossDcConfig | None = None,
    on_stage: StageHook | None = None,
) -> CrossDagPlan:
    """从逻辑 DAG 开始的确定性编译。无 LLM，可单测。"""
    resolved_config = config or get_cross_dc_config()
    emit = on_stage or (lambda stage, payload: None)

    emit("bind", {"status": "started"})
    bind_result = bind_centers(
        logical_dag,
        intent,
        default_center_id=resolved_config.default_center_id,
        known_centers=set(resolved_config.centers) or None,
        replica_weights=resolved_config.replica_weights or None,
        available_statuses=resolved_config.available_statuses or None,
        metric_directions=resolved_config.metric_directions or None,
    )
    emit(
        "bind",
        {
            "status": "finished",
            "center_of": dict(bind_result.center_of),
            "reasons": dict(bind_result.reasons),
            "replica_decisions": [d.to_json() for d in bind_result.replica_decisions],
        },
    )

    emit("segment", {"status": "started"})
    graph = build_segment_graph(logical_dag, bind_result.center_of)
    emit(
        "segment",
        {
            "status": "finished",
            "segment_count": len(graph.segments),
            "cross_edge_count": len(graph.cross_edges),
            "segments": graph.to_json(),
        },
    )

    emit("nest", {"status": "started"})
    endpoint_of = {
        center_id: center.grpc_endpoint
        for center_id, center in resolved_config.centers.items()
    }
    nested_dsl, nest_count = build_nested_dsl(
        logical_dag,
        graph,
        endpoint_of=endpoint_of,
        export_dir=resolved_config.export_dir,
        task_id=plan_id,
        task_name=logical_dag.task_name or "跨域任务",
        wait_timeout_seconds=resolved_config.subdag_wait_timeout_seconds,
    )
    emit(
        "nest",
        {
            "status": "finished",
            "depth": _depth_of(nested_dsl),
            "nest_count": dict(nest_count),
            "nested_dsl": nested_dsl,
        },
    )

    emit("validate", {"status": "started"})
    report = ValidationReport()
    report.merge(
        validate_location_hints(
            intent, bind_result.center_of, resolved_config.location_term
        )
    )
    report.merge(validate_segmentation(logical_dag, graph, nest_count))
    report.merge(validate_nested_dsl(nested_dsl))
    emit("validate", {"status": "finished", "report": report.to_json()})

    if not report.ok:
        log.warning("跨域规划校验未通过 plan_id=%s errors=%s", plan_id, report.errors)

    return CrossDagPlan(
        plan_id=plan_id,
        intent=intent,
        logical_dag=logical_dag,
        bind_result=bind_result,
        segment_graph=graph,
        nested_dsl=nested_dsl,
        validation=report,
    )


async def stream_plan_cross_dag(
    user_request: str,
    **kwargs: Any,
) -> AsyncIterator[dict[str, Any]]:
    """SSE 版本。事件结构对齐 runtime/planner_engine.py 的 stream_chat。"""
    import asyncio

    events: list[dict[str, Any]] = []

    def collect(stage: str, payload: dict[str, Any]) -> None:
        events.append({"type": "stage", "stage": stage, **payload})

    yield {"type": "status", "stage": "started"}

    loop = asyncio.get_running_loop()
    pending: list[CrossDagPlan] = []
    error: list[Exception] = []

    def run() -> None:
        try:
            pending.append(plan_cross_dag(user_request, on_stage=collect, **kwargs))
        except Exception as exc:
            error.append(exc)

    task = loop.run_in_executor(None, run)
    emitted = 0
    while not task.done() or emitted < len(events):
        while emitted < len(events):
            yield events[emitted]
            emitted += 1
        if task.done():
            break
        await asyncio.sleep(0.05)
    await task

    while emitted < len(events):
        yield events[emitted]
        emitted += 1

    if error:
        yield {"type": "error", "message": str(error[0])}
        return

    plan = pending[0]
    yield {"type": "done", "plan": plan.to_json()}


def _depth_of(dsl: dict[str, Any]) -> int:
    """嵌套层数，用于日志和前端展示。"""
    import json as _json

    from .schema import REMOTE_NODE_PREFIX

    depth = 1
    for node in dsl.get("nodes") or []:
        if not str(node.get("node_id", "")).startswith(REMOTE_NODE_PREFIX):
            continue
        for param in node.get("input_params") or []:
            if param.get("param_name") != "subdag_definition_json":
                continue
            try:
                child = _json.loads(param.get("param_value") or "{}")
            except Exception:
                continue
            depth = max(depth, 1 + _depth_of(child))
    return depth
