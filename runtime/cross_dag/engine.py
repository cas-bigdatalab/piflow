"""跨域规划流水线编排。"""

from __future__ import annotations

import logging
import uuid
from typing import Any, AsyncIterator, Callable

from .binder import bind_centers
from .config import CrossDcConfig, get_cross_dc_config, resolve_cross_dc_config
from .intent import plan_global_dag, recognize_intent
from .nester import build_nested_dsl
from .planner_bridge import (
    database_param_resolver,
    database_skill_resolver,
    expand_planning_json,
    normalize_dataset_source_contracts,
)
from .registry_stub import DatasourceRegistry, get_registry, refresh_registry
from .satisfaction import analyze_satisfaction
from .schema import (
    MODE_COMPOSITION,
    MODE_DIRECT,
    MODE_UNAVAILABLE,
    BindResult,
    CrossDagError,
    CrossDagPlan,
    DirectAccess,
    IntentDataset,
    IntentSpec,
    LogicalDag,
    ReplicaCandidate,
    SatisfactionReport,
    SegmentGraph,
    ValidationReport,
    build_execution_dsl,
)
from .segmenter import build_segment_graph
from .selector import select_replica
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
    # One fresh directory snapshot per planning request. The adapter then
    # caches that snapshot for all reads in this request.
    resolved_registry = refresh_registry(registry or get_registry())
    resolved_config = resolve_cross_dc_config(
        config or get_cross_dc_config(), resolved_registry
    )
    emit = on_stage or (lambda stage, payload: None)

    emit("intent", {"status": "started"})
    resolved_intent = intent or recognize_intent(
        user_request,
        llm=llm,
        registry=resolved_registry,
        config=resolved_config,
    )
    emit("intent", {"status": "finished", "intent": resolved_intent.to_json()})

    emit("satisfaction", {"status": "started"})
    satisfaction = analyze_satisfaction(
        resolved_intent, config=resolved_config, registry=resolved_registry
    )
    emit(
        "satisfaction",
        {
            "status": "finished",
            "mode": satisfaction.mode,
            "reason": satisfaction.reason,
            "satisfaction": satisfaction.to_json(),
        },
    )

    # 平台里根本没有相关数据时，这是一个正常结论，不是错误：直接给结果，
    # 不要再花一次 LLM 去规划一个注定失败的 DAG。
    if satisfaction.mode == MODE_UNAVAILABLE and planning_json is None:
        return build_unavailable_plan(
            resolved_intent, satisfaction, plan_id=resolved_plan_id, on_stage=emit
        )

    # 有数据集能独立满足全部需求、且不需要任何加工时，不生成 DAG，直接给访问路由。
    if satisfaction.mode == MODE_DIRECT and planning_json is None:
        return build_direct_plan(
            resolved_intent,
            satisfaction,
            plan_id=resolved_plan_id,
            config=resolved_config,
            registry=resolved_registry,
            on_stage=emit,
        )

    emit("planning", {"status": "started"})
    resolved_planning = planning_json or plan_global_dag(
        resolved_intent,
        llm=llm,
        config=resolved_config,
    )
    emit("planning", {"status": "finished", "planning_json": resolved_planning})

    emit("expand", {"status": "started"})
    logical_dag = expand_planning_json(
        resolved_planning,
        skill_resolver=skill_resolver or database_skill_resolver(),
        param_resolver=database_param_resolver(),
        task_id=resolved_plan_id,
    )
    contract_warnings = normalize_dataset_source_contracts(
        logical_dag,
        resolved_intent,
    )
    logical_report = validate_logical_dag(
        logical_dag,
        sink_skills=resolved_config.sink_skills,
        placeholder_skills=resolved_config.placeholder_skills,
    )
    for warning in contract_warnings:
        logical_report.warn(warning)
    if not logical_report.ok:
        raise CrossDagError("逻辑 DAG 校验失败:\n" + "\n".join(logical_report.errors))
    logical_report.merge(validate_intent_coverage(resolved_intent, logical_dag))
    emit(
        "expand",
        {
            "status": "finished",
            "node_count": len(logical_dag.nodes),
            "binding_count": len(logical_dag.bindings),
            "warnings": list(logical_report.warnings),
            "errors": list(logical_report.errors),
            "description": logical_dag.description,
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
    plan.satisfaction = satisfaction
    # 满足分析的提醒（元数据没声明、需求取值全目录都找不到）统一走校验告警，
    # 和另外两条分支一致 —— 提示语只在一个地方出现，前端也只需要读一处。
    for note in satisfaction.notes:
        if note not in plan.validation.warnings:
            plan.validation.warn(note)
    return plan


def build_unavailable_plan(
    intent: IntentSpec,
    satisfaction: SatisfactionReport,
    *,
    plan_id: str,
    on_stage: StageHook | None = None,
) -> CrossDagPlan:
    """平台没有相关数据 —— 这是正常结论，不是错误。

    用户不可能每次都问平台正好有的数据。把它当异常抛出去，前端只能显示一个
    红色报错；当成一种结果状态返回，前端才能好好告诉用户缺什么、检索了多少。
    """
    emit = on_stage or (lambda stage, payload: None)
    emit("unavailable", {"status": "started"})

    report = ValidationReport()
    for note in satisfaction.notes:
        report.warn(note)

    emit(
        "unavailable",
        {
            "status": "finished",
            "reason": satisfaction.reason,
            "missing_values": satisfaction.missing_values,
            "scanned_count": satisfaction.scanned_count,
            "report": report.to_json(),
        },
    )

    return CrossDagPlan(
        plan_id=plan_id,
        intent=intent,
        logical_dag=LogicalDag(task_name=intent.goal or "无可用数据", task_id=plan_id),
        bind_result=BindResult(),
        segment_graph=SegmentGraph(),
        nested_dsl={},
        validation=report,
        mode=MODE_UNAVAILABLE,
        satisfaction=satisfaction,
    )


def build_direct_plan(
    intent: IntentSpec,
    satisfaction: SatisfactionReport,
    *,
    plan_id: str,
    config: CrossDcConfig | None = None,
    registry: DatasourceRegistry | None = None,
    on_stage: StageHook | None = None,
) -> CrossDagPlan:
    """直接获取：不生成 DAG，只挑数据集和副本。确定性，可单测。"""
    resolved_config = config or get_cross_dc_config()
    resolved_registry = registry or get_registry()
    emit = on_stage or (lambda stage, payload: None)

    emit("access", {"status": "started"})

    matches = satisfaction.full_matches
    if not matches:
        raise CrossDagError("直接获取要求存在完整满足需求的数据集，但满足分析没有给出")

    # 目标优先取意图挑中的那个 —— 模型读过描述，它的选择往往比字段比对更贴题；
    # 模型一个都没挑中时，才用后端扫目录补出来的完整匹配。
    ordered = [c for c in matches if c.selected] + [c for c in matches if not c.selected]
    target = ordered[0]
    dataset = _resolve_intent_dataset(intent, target.dataset_id, resolved_registry)
    if dataset is None:
        raise CrossDagError(
            f"满足分析给出的数据集 {target.dataset_id} 在意图和注册表里都找不到"
        )

    # 用户点名了位置就优先取那儿的副本，否则就近取本地。
    preferred = resolved_config.default_center_id
    for hint in intent.location_hints:
        if hint.center_id and resolved_config.has_center(hint.center_id):
            preferred = hint.center_id
            break

    decision = select_replica(
        dataset,
        preferred_center_id=preferred,
        node_id=dataset.dataset_id,
        weights=resolved_config.replica_weights or None,
        directions=resolved_config.metric_directions or None,
        known_centers=set(resolved_config.centers) or None,
        available_statuses=resolved_config.available_statuses or None,
    )

    direct_access = DirectAccess(
        dataset_id=dataset.dataset_id,
        name=dataset.name,
        alias=dataset.alias,
        replica_decision=decision,
        alternatives=[
            {
                "dataset_id": cover.dataset_id,
                "name": cover.name,
                "alias": cover.alias,
                "selected": cover.selected,
                "covered_count": cover.covered_count,
                "required_count": cover.required_count,
            }
            for cover in ordered[1:]
        ],
    )

    report = ValidationReport()
    report.merge(
        validate_location_hints(
            intent,
            {dataset.dataset_id: decision.chosen.center_id},
            resolved_config.location_term,
        )
    )
    for note in satisfaction.notes:
        report.warn(note)

    emit(
        "access",
        {
            "status": "finished",
            "dataset_id": dataset.dataset_id,
            "replica": decision.chosen.replica_id,
            "center_id": decision.chosen.center_id,
            "alternatives": len(direct_access.alternatives),
            "direct_access": direct_access.to_json(),
            "report": report.to_json(),
        },
    )

    return CrossDagPlan(
        plan_id=plan_id,
        intent=intent,
        logical_dag=LogicalDag(task_name=intent.goal or "直接获取", task_id=plan_id),
        bind_result=BindResult(replica_decisions=[decision]),
        segment_graph=SegmentGraph(),
        nested_dsl={},
        validation=report,
        mode=MODE_DIRECT,
        satisfaction=satisfaction,
        direct_access=direct_access,
    )


def _resolve_intent_dataset(
    intent: IntentSpec,
    dataset_id: str,
    registry: DatasourceRegistry,
) -> IntentDataset | None:
    """按 dataset_id 取数据集。意图里没有就回注册表补 —— 覆盖判定是对全量目录做的，
    完整匹配的那个未必是模型挑出来的。"""
    for dataset in intent.datasets:
        if dataset.dataset_id == dataset_id:
            return dataset

    record = registry.get_dataset(dataset_id)
    if record is None:
        return None
    return IntentDataset(
        alias=dataset_id,
        dataset_id=record.dataset_id,
        source_id=record.source_id,
        center_id=record.center_id,
        locator=record.locator,
        name=record.name,
        replicas=[ReplicaCandidate.from_json(r.to_json()) for r in record.replicas],
        facets={str(k): [str(x) for x in v] for k, v in (record.facets or {}).items()},
        source_skill=record.source_skill,
        source_param=record.source_param,
        source_output_param=record.source_output_param,
    )


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
    execution_dsl = build_execution_dsl(
        logical_dag,
        task_id=plan_id,
        task_name=logical_dag.task_name or "跨域任务",
    )
    emit(
        "nest",
        {
            "status": "finished",
            "depth": _depth_of(nested_dsl),
            "nest_count": dict(nest_count),
            "execution_dsl": execution_dsl,
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
    report.merge(validate_nested_dsl(execution_dsl))
    report.merge(validate_nested_dsl(nested_dsl))

    roots = graph.root_segments()
    execution_center_id = (
        graph.segments[roots[0]].center_id if len(roots) == 1 else ""
    )
    execution_grpc_endpoint = ""
    if execution_center_id:
        try:
            execution_grpc_endpoint = resolved_config.endpoint_of(execution_center_id)
        except KeyError as exc:
            report.error(str(exc))
    if execution_center_id and not execution_grpc_endpoint:
        report.error(
            f"最外层执行位置 {execution_center_id} 没有 gRPC 地址，无法提交执行"
        )
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
        execution_dsl=execution_dsl,
        execution_center_id=execution_center_id,
        execution_grpc_endpoint=execution_grpc_endpoint,
        center_endpoints=endpoint_of,
    )


async def stream_plan_cross_dag(
    user_request: str,
    *,
    detail: bool = False,
    on_plan: Any = None,
    **kwargs: Any,
) -> AsyncIterator[dict[str, Any]]:
    """SSE 版本。事件结构对齐 runtime/planner_engine.py 的 stream_chat。

    阶段事件推的是一行摘要而不是全量载荷：步骤条上只显示一行字，把整个嵌套
    DSL 和打分表逐阶段推给浏览器纯属噪音。完整结果在最后的 done 事件里一次
    给到，需要内部细节时传 detail=True。
    """
    import asyncio

    from .plan_view import build_plan_view, stage_brief

    events: list[dict[str, Any]] = []

    def collect(stage: str, payload: dict[str, Any]) -> None:
        if detail:
            events.append({"type": "stage", "stage": stage, **payload})
        else:
            events.append({"type": "stage", **stage_brief(stage, payload)})

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
    if on_plan is not None:
        # 交给调用方落缓存/落库，runtime 不反过来依赖 services
        on_plan(plan)
    yield {"type": "done", "plan": build_plan_view(plan, detail=detail)}


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
