"""跨域规划服务层。"""

from __future__ import annotations

import json
import logging
import threading
import uuid
from typing import Any

from runtime.cross_dag.config import get_cross_dc_config
from runtime.cross_dag.engine import plan_cross_dag
from runtime.cross_dag.registry_stub import get_registry
from runtime.cross_dag.schema import CrossDagError, CrossDagPlan

log = logging.getLogger("flow.cross_dag.service")

_PLAN_CACHE: dict[str, CrossDagPlan] = {}
_CACHE_LOCK = threading.Lock()
_CACHE_LIMIT = 100


def create_cross_dag_plan(*, user_request: str, user_id: str) -> dict[str, Any]:
    """只规划不执行，返回可预览的完整计划。"""
    plan = plan_cross_dag(user_request)
    _remember(plan)
    log.info(
        "cross dag planned plan_id=%s user_id=%s segments=%s valid=%s",
        plan.plan_id,
        user_id,
        len(plan.segment_graph.segments),
        plan.validation.ok,
    )
    return _summarize(plan)


def compile_cross_dag_plan(
    *,
    planning_json: dict[str, Any],
    user_id: str,
    dataset_ids: list[str] | None = None,
) -> dict[str, Any]:
    """跳过 LLM，直接从规划态 JSON 编译。"""
    from runtime.cross_dag.engine import compile_cross_dag
    from runtime.cross_dag.planner_bridge import expand_planning_json
    from runtime.cross_dag.schema import IntentDataset, IntentSpec, ReplicaCandidate
    from runtime.cross_dag.validator import validate_logical_dag

    plan_id = f"xdc-compile-{uuid.uuid4().hex[:8]}"
    registry = get_registry()

    wanted = list(dataset_ids or _scan_dataset_ids(planning_json))
    datasets: list[IntentDataset] = []
    missing: list[str] = []
    for dataset_id in wanted:
        record = registry.get_dataset(dataset_id)
        if record is None:
            missing.append(dataset_id)
            continue
        datasets.append(
            IntentDataset(
                alias=dataset_id,
                dataset_id=record.dataset_id,
                source_id=record.source_id,
                center_id=record.center_id,
                locator=record.locator,
                name=record.name,
                replicas=[ReplicaCandidate.from_json(r.to_json()) for r in record.replicas],
            )
        )
    if missing:
        raise CrossDagError(f"规划中引用了未注册的数据集: {missing}")

    intent = IntentSpec(
        goal=str((planning_json.get("task") or {}).get("name") or "compile-only"),
        datasets=datasets,
        assumptions=["由 /xdc/compile 直接编译，未经过意图识别与 LLM 规划"],
    )

    logical = expand_planning_json(planning_json, task_id=plan_id)

    logical_report = validate_logical_dag(logical)
    if not logical_report.ok:
        raise CrossDagError("逻辑 DAG 校验失败:\n" + "\n".join(logical_report.errors))

    plan = compile_cross_dag(logical, intent=intent, plan_id=plan_id)
    plan.validation.merge(logical_report)
    _remember(plan)
    log.info(
        "cross dag compiled plan_id=%s user_id=%s datasets=%s valid=%s",
        plan_id, user_id, [d.dataset_id for d in datasets], plan.validation.ok,
    )
    return _summarize(plan)


def _scan_dataset_ids(planning_json: dict[str, Any]) -> list[str]:
    """从规划 JSON 里扫出所有 dataset://<id> 引用，保持出现顺序去重。"""
    from runtime.cross_dag.schema import DATASET_URI_PREFIX

    found: list[str] = []
    for node in planning_json.get("nodes") or []:
        for value in (node.get("params") or {}).values():
            if not isinstance(value, str) or not value.startswith(DATASET_URI_PREFIX):
                continue
            dataset_id = value[len(DATASET_URI_PREFIX):].strip().strip("/")
            if dataset_id and dataset_id not in found:
                found.append(dataset_id)
    return found


def handoff_check_cross_dag_plan(plan_id: str) -> dict[str, Any]:
    """执行引擎对接自检：把嵌套 DSL 每一层都真正走一遍引擎的转换与构图。"""
    from piflow_engine.cn.piflow.core.frontend_dag_converter import (
        convert_frontend_dag_to_piflow,
    )

    plan = _PLAN_CACHE.get(plan_id)
    if plan is None:
        raise CrossDagError(f"计划不存在或已过期: {plan_id}")

    flow_bean = None
    construct_note = ""
    try:
        from piflow_engine.cn.piflow.core.flow_bean import FlowBean

        flow_bean = FlowBean
    except Exception as exc:
        construct_note = f"构图不可用（{type(exc).__name__}: {exc}），本次只验证了转换"

    resolver = None
    resolver_note = ""
    try:
        from tools.excutor.excutor_utils import resolve_dag_definition_skills

        resolver = resolve_dag_definition_skills
    except Exception as exc:
        resolver_note = f"skill 解析不可用（{type(exc).__name__}: {exc}），已降级"

    layers: list[dict[str, Any]] = []
    root_center = get_cross_dc_config().local_center_id
    for depth, name, center_id, layer in _iter_dsl_layers(plan.nested_dsl, center_id=root_center):
        entry: dict[str, Any] = {
            "depth": depth,
            "执行位置": center_id,
            "层名": name,
            "节点数": len(layer.get("nodes") or []),
            "绑定数": len(layer.get("bindings") or []),
        }

        resolved = layer
        if resolver is not None:
            try:
                resolved = resolver(layer)
            except Exception as exc:
                entry["skill解析"] = f"降级: {type(exc).__name__}: {exc}"
                resolved = layer
        elif resolver_note:
            entry["skill解析"] = resolver_note

        entry["按类路径加载"] = [
            str((n.get("skill") or {}).get("skill_id", ""))
            for n in resolved.get("nodes") or []
            if not str((n.get("skill") or {}).get("skill_id", "")).endswith(".json")
        ]

        try:
            piflow_json = convert_frontend_dag_to_piflow(resolved)
        except Exception as exc:
            entry["ok"] = False
            entry["失败环节"] = "转换"
            entry["错误"] = f"{type(exc).__name__}: {exc}"
            layers.append(entry)
            continue

        flow = (piflow_json.get("flow") or {})
        entry["stops"] = len(flow.get("stops") or [])
        entry["paths"] = len(flow.get("paths") or [])

        mismatch = []
        if entry["stops"] != entry["节点数"]:
            mismatch.append(f"stops({entry['stops']}) != nodes({entry['节点数']})")
        if entry["paths"] != entry["绑定数"]:
            mismatch.append(f"paths({entry['paths']}) != bindings({entry['绑定数']})")
        if mismatch:
            entry["ok"] = False
            entry["失败环节"] = "转换"
            entry["错误"] = "；".join(mismatch)
            layers.append(entry)
            continue

        if flow_bean is None:
            entry["ok"] = True
            entry["构图"] = construct_note
            layers.append(entry)
            continue

        try:
            flow_bean.from_dict(piflow_json).construct_flow()
        except Exception as exc:
            entry["ok"] = False
            entry["失败环节"] = "构图"
            entry["错误"] = f"{type(exc).__name__}: {exc}"
            layers.append(entry)
            continue

        entry["ok"] = True
        layers.append(entry)

    bad = [item for item in layers if not item.get("ok")]
    notes = [
        "这一步走的是执行引擎的真实转换与构图代码，不是模拟",
        "不提交执行、不连 gRPC、不读数据文件",
        "全绿说明 DSL 引擎能收；真跑还需要源文件到位、远端数据源已启动",
    ]
    if flow_bean is None:
        notes.append("本次只验证到转换层，构图未执行 —— 结论不完整")
    return {
        "plan_id": plan.plan_id,
        "ok": not bad,
        "转换已执行": True,
        "构图已执行": flow_bean is not None,
        "层数": len(layers),
        "失败层数": len(bad),
        "layers": layers,
        "说明": notes,
    }


def _iter_dsl_layers(dsl: dict[str, Any], depth: int = 0, center_id: str = ""):
    """深度优先遍历嵌套 DSL，产出 (层深, 层名, 执行位置, 该层 DSL)。"""
    from runtime.cross_dag.schema import REMOTE_NODE_PREFIX

    name = str((dsl.get("task") or {}).get("dag_task_name") or f"第{depth}层")
    yield depth, name, center_id, dsl

    for node in dsl.get("nodes") or []:
        node_id = str(node.get("node_id", ""))
        if not node_id.startswith(REMOTE_NODE_PREFIX):
            continue
        params = {
            str(p.get("param_name")): p.get("param_value")
            for p in node.get("input_params") or []
        }
        raw_child = params.get("subdag_definition_json") or ""
        try:
            child = json.loads(raw_child) if isinstance(raw_child, str) else {}
        except json.JSONDecodeError:
            continue
        if child:
            yield from _iter_dsl_layers(
                child, depth + 1, str(params.get("remote_grpc_target") or "")
            )


def get_cross_dag_plan(plan_id: str) -> dict[str, Any]:
    plan = _PLAN_CACHE.get(plan_id)
    if plan is None:
        raise CrossDagError(f"计划不存在或已过期: {plan_id}")
    return _summarize(plan)


def execute_cross_dag_plan(*, plan_id: str, user_id: str) -> dict[str, Any]:
    """把最外层嵌套 DSL 交给现有执行链路。"""
    from services.dag_panel_service import save_dag_panel
    from services.dag_runtime_service import run_dag_task

    plan = _PLAN_CACHE.get(plan_id)
    if plan is None:
        raise CrossDagError(f"计划不存在或已过期: {plan_id}")

    if not plan.validation.ok:
        raise CrossDagError(
            "计划未通过校验，拒绝执行:\n" + "\n".join(plan.validation.errors)
        )

    saved = save_dag_panel(
        definition_json=plan.nested_dsl,
        create_user_id=user_id,
    )
    dag_task_id = saved["task_id"]

    result = run_dag_task(
        create_user_id=user_id,
        dag_task_id=dag_task_id,
    )

    log.info(
        "cross dag submitted plan_id=%s dag_task_id=%s process_id=%s",
        plan.plan_id,
        dag_task_id,
        result.get("process_id"),
    )
    return {
        "plan_id": plan.plan_id,
        "dag_task_id": dag_task_id,
        "process_id": result.get("process_id"),
        "status": result.get("status"),
        "warnings": list(plan.validation.warnings),
    }


def list_cross_dag_context() -> dict[str, Any]:
    """中心清单 + 数据集清单，供前端展示和排障。"""
    config = get_cross_dc_config()
    registry = get_registry()
    return {
        "local_center_id": config.local_center_id,
        "default_center_id": config.default_center_id,
        "centers": [
            {
                "center_id": center.center_id,
                "center_name": center.center_name,
                "grpc_endpoint": center.grpc_endpoint,
            }
            for center in config.centers.values()
        ],
        "datasets": [item.to_json() for item in registry.list_datasets()],
    }


def _summarize(plan: CrossDagPlan) -> dict[str, Any]:
    payload = plan.to_json()
    payload["summary"] = {
        "node_count": len(plan.logical_dag.nodes),
        "segment_count": len(plan.segment_graph.segments),
        "cross_edge_count": len(plan.segment_graph.cross_edges),
        "centers": sorted({s.center_id for s in plan.segment_graph.segments.values()}),
    }
    return payload


def _remember(plan: CrossDagPlan) -> None:
    with _CACHE_LOCK:
        if len(_PLAN_CACHE) >= _CACHE_LIMIT:
            for stale in list(_PLAN_CACHE)[: _CACHE_LIMIT // 2]:
                _PLAN_CACHE.pop(stale, None)
        _PLAN_CACHE[plan.plan_id] = plan
