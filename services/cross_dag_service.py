"""跨域规划服务层。"""

from __future__ import annotations

import json
import logging
import threading
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, AsyncIterator, Callable
from urllib.parse import urlencode

from infra.config_loader import resolve_workspace_root
from runtime.cross_dag.config import get_cross_dc_config, resolve_cross_dc_config
from runtime.cross_dag.engine import (
    finalize_cross_dag_pre_bind,
    plan_cross_dag,
    plan_cross_dag_pre_bind,
)
from runtime.cross_dag.registry_stub import get_registry, refresh_registry
from runtime.cross_dag.schema import (
    MODE_DIRECT,
    MODE_UNAVAILABLE,
    CrossDagError,
    CrossDagPlan,
    CrossDagPreBindPlan,
)

log = logging.getLogger("flow.cross_dag.service")

_PLAN_CACHE: dict[str, CrossDagPlan] = {}
_PRE_BIND_CACHE: dict[str, tuple[str, CrossDagPreBindPlan]] = {}
_CACHE_LOCK = threading.Lock()
_CACHE_LIMIT = 100


class CrossDagExecutionNotFound(LookupError):
    """The process id has no registered cross-domain execution."""


class CrossDagExecutionNotReady(RuntimeError):
    """The requested result is not downloadable yet."""


class DirectDatasetSelectionRequired(CrossDagError):
    """A direct pre-bind plan must receive an explicit dataset choice."""


class InvalidDirectDatasetSelection(CrossDagError):
    """The selected dataset is not one of the direct full-match candidates."""


def validate_direct_dataset_selection(
    pre_bind: CrossDagPreBindPlan,
    selected_dataset_id: str | None,
) -> str:
    """Validate a Direct dataset choice without changing task or plan state."""
    if pre_bind.mode != MODE_DIRECT:
        return ""

    normalized = str(selected_dataset_id or "").strip()
    candidate_ids = [
        coverage.dataset_id
        for coverage in pre_bind.satisfaction.full_matches
        if coverage.dataset_id
    ]
    if not normalized:
        raise DirectDatasetSelectionRequired(
            "Direct 模式需要先选择数据集；"
            f"可选 dataset_id：{candidate_ids}"
        )
    if normalized not in candidate_ids:
        raise InvalidDirectDatasetSelection(
            f"所选数据集 {normalized} 不在 Direct 完整匹配候选中；"
            f"可选 dataset_id：{candidate_ids}"
        )
    return normalized


@dataclass(frozen=True)
class CrossDagResultDownload:
    path: Path
    file_name: str
    media_type: str


def create_cross_dag_plan(
    *, user_request: str, user_id: str, detail: bool = False
) -> dict[str, Any]:
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
    return _summarize(plan, detail=detail)


def create_cross_dag_pre_bind_plan(
    *,
    user_request: str,
    user_id: str,
    detail: bool = False,
) -> dict[str, Any]:
    """Plan through logical DAG expansion without selecting any replica."""
    pre_bind = plan_cross_dag_pre_bind(user_request)
    _remember_pre_bind(pre_bind, user_id=user_id)
    log.info(
        "cross dag pre-bind planned plan_id=%s user_id=%s mode=%s nodes=%s valid=%s",
        pre_bind.plan_id,
        user_id,
        pre_bind.mode,
        len(pre_bind.logical_dag.nodes),
        pre_bind.validation.ok,
    )
    return _summarize_pre_bind(pre_bind, detail=detail)


def bind_and_execute_cross_dag_pre_bind(
    *,
    plan_id: str,
    user_id: str,
    detail: bool = False,
    selected_dataset_id: str | None = None,
) -> dict[str, Any]:
    """Bind through validation and immediately submit the resulting plan."""
    pre_bind = _get_owned_pre_bind(plan_id=plan_id, user_id=user_id)
    plan, execution = _finalize_and_execute_pre_bind(
        pre_bind,
        user_id=user_id,
        selected_dataset_id=selected_dataset_id,
    )
    return {
        "plan": _summarize(plan, detail=detail),
        "execution": execution,
    }


def _finalize_and_execute_pre_bind(
    pre_bind: CrossDagPreBindPlan,
    *,
    user_id: str,
    on_stage: Callable[[str, dict[str, Any]], None] | None = None,
    selected_dataset_id: str | None = None,
) -> tuple[CrossDagPlan, dict[str, Any]]:
    """Shared second phase used by both JSON and SSE endpoints."""
    if pre_bind.mode == MODE_UNAVAILABLE:
        raise CrossDagError("该预规划没有可用数据，不能进行副本绑定和提交执行")
    if not pre_bind.validation.ok:
        raise CrossDagError(
            "预绑定规划未通过校验，拒绝继续:\n"
            + "\n".join(pre_bind.validation.errors)
        )

    normalized_dataset_id = validate_direct_dataset_selection(
        pre_bind,
        selected_dataset_id,
    )
    plan = finalize_cross_dag_pre_bind(
        pre_bind,
        on_stage=on_stage,
        selected_dataset_id=normalized_dataset_id or None,
    )
    _remember(plan)

    if on_stage is not None:
        on_stage("submit", {"status": "started", "mode": plan.mode})
    execution = execute_cross_dag_plan(plan_id=plan.plan_id, user_id=user_id)
    if on_stage is not None:
        on_stage(
            "submit",
            {
                "status": "finished",
                "mode": plan.mode,
                "process_id": execution.get("process_id", ""),
                "submit_status": execution.get("status", ""),
            },
        )
    return plan, execution


def _finalize_and_execute_direct_pre_bind(
    pre_bind: CrossDagPreBindPlan,
    *,
    user_id: str,
    on_stage: Callable[[str, dict[str, Any]], None] | None = None,
    selected_dataset_id: str | None = None,
) -> tuple[CrossDagPlan, dict[str, Any]]:
    """Session-only direct path: bind one replica and submit one source node.

    The existing two-phase helper above remains the sole composition path.
    Keeping this entry point separate also preserves the legacy direct API,
    which returns an access route without creating an executor process.
    """
    if pre_bind.mode != MODE_DIRECT:
        raise CrossDagError("direct execution helper only accepts direct plans")
    if not pre_bind.validation.ok:
        raise CrossDagError(
            "预绑定规划未通过校验，拒绝继续\n"
            + "\n".join(pre_bind.validation.errors)
        )

    normalized_dataset_id = validate_direct_dataset_selection(
        pre_bind,
        selected_dataset_id,
    )
    plan = finalize_cross_dag_pre_bind(
        pre_bind,
        on_stage=on_stage,
        selected_dataset_id=normalized_dataset_id,
    )
    if plan.mode != MODE_DIRECT:
        raise CrossDagError(f"expected direct plan, got {plan.mode}")

    if on_stage is not None:
        on_stage("submit", {"status": "started", "mode": plan.mode})
    execution = execute_direct_session_plan(plan=plan, user_id=user_id)
    if on_stage is not None:
        on_stage(
            "submit",
            {
                "status": "finished",
                "mode": plan.mode,
                "process_id": execution.get("process_id", ""),
                "submit_status": execution.get("status", ""),
            },
        )
    return plan, execution


def compile_cross_dag_plan(
    *,
    planning_json: dict[str, Any],
    user_id: str,
    detail: bool = False,
    dataset_ids: list[str] | None = None,
) -> dict[str, Any]:
    """跳过 LLM，直接从规划态 JSON 编译。"""
    from runtime.cross_dag.engine import compile_cross_dag
    from runtime.cross_dag.planner_bridge import expand_planning_json
    from runtime.cross_dag.schema import IntentDataset, IntentSpec, ReplicaCandidate
    from runtime.cross_dag.validator import validate_logical_dag

    plan_id = f"xdc-compile-{uuid.uuid4().hex[:8]}"
    registry = refresh_registry(get_registry())

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
                source_skill=record.source_skill,
                source_param=record.source_param,
                source_output_param=record.source_output_param,
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

    config = get_cross_dc_config()
    logical_report = validate_logical_dag(
        logical,
        sink_skills=config.sink_skills,
        placeholder_skills=config.placeholder_skills,
    )
    if not logical_report.ok:
        raise CrossDagError("逻辑 DAG 校验失败:\n" + "\n".join(logical_report.errors))

    config = resolve_cross_dc_config(get_cross_dc_config(), registry)
    plan = compile_cross_dag(
        logical,
        intent=intent,
        plan_id=plan_id,
        config=config,
    )
    plan.validation.merge(logical_report)
    _remember(plan)
    log.info(
        "cross dag compiled plan_id=%s user_id=%s datasets=%s valid=%s",
        plan_id, user_id, [d.dataset_id for d in datasets], plan.validation.ok,
    )
    return _summarize(plan, detail=detail)


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

    from runtime.cross_dag.schema import MODE_COMPOSITION

    plan = _PLAN_CACHE.get(plan_id)
    if plan is None:
        raise CrossDagError(f"计划不存在或已过期: {plan_id}")

    if plan.mode != MODE_COMPOSITION:
        return {
            "plan_id": plan.plan_id,
            "mode": plan.mode,
            "ok": True,
            "层数": 0,
            "失败层数": 0,
            "layers": [],
            "说明": [
                f"{plan.mode} 计划不生成 DAG，没有需要交给执行引擎的结构，本项自检不适用",
            ],
        }

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
    roots = plan.segment_graph.root_segments()
    root_center = (
        plan.segment_graph.segments[roots[0]].center_id if len(roots) == 1 else ""
    )
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
        "最外层绑定位置": root_center,
        "根提交地址已确定": bool(plan.execution_grpc_endpoint),
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


def get_cross_dag_plan(plan_id: str, *, detail: bool = False) -> dict[str, Any]:
    plan = _PLAN_CACHE.get(plan_id)
    if plan is None:
        raise CrossDagError(f"计划不存在或已过期: {plan_id}")
    return _summarize(plan, detail=detail)


def get_cross_dag_pre_bind_plan(
    plan_id: str, *, user_id: str
) -> dict[str, Any]:
    """Return the user-owned frontend snapshot before replica binding."""
    try:
        pre_bind = _get_owned_pre_bind(plan_id=plan_id, user_id=user_id)
    except CrossDagError:
        from repositories import xdc_session_repository

        snapshot = xdc_session_repository.get_pre_bind_view_by_plan_id(
            plan_id=plan_id,
            user_id=str(user_id),
        )
        if snapshot is None:
            raise CrossDagError(f"预绑定计划不存在或已过期: {plan_id}")
        return dict(snapshot.get("payload_json") or {})
    return _summarize_pre_bind(pre_bind, detail=False)


def execute_cross_dag_plan(*, plan_id: str, user_id: str) -> dict[str, Any]:
    """把最外层嵌套 DSL 交给现有执行链路。直接获取的计划没有 DAG，只回访问路由。"""
    from runtime.cross_dag.schema import MODE_DIRECT, MODE_UNAVAILABLE

    plan = _PLAN_CACHE.get(plan_id)
    if plan is None:
        raise CrossDagError(f"计划不存在或已过期: {plan_id}")

    if plan.mode == MODE_UNAVAILABLE:
        missing = plan.satisfaction.missing_values if plan.satisfaction else []
        raise CrossDagError(
            "平台当前没有满足该需求的数据，没有可执行的方案"
            + (f"。缺少：{missing}" if missing else "")
        )

    if not plan.validation.ok:
        raise CrossDagError(
            "计划未通过校验，拒绝执行:\n" + "\n".join(plan.validation.errors)
        )

    if plan.mode == MODE_DIRECT:
        access = plan.direct_access
        if access is None or access.replica_decision is None:
            raise CrossDagError("直接获取的计划缺少访问路由")
        chosen = access.replica_decision.chosen
        log.info(
            "cross dag direct access plan_id=%s dataset=%s replica=%s",
            plan.plan_id,
            access.dataset_id,
            chosen.replica_id if chosen else "",
        )
        return {
            "plan_id": plan.plan_id,
            "mode": plan.mode,
            "dataset_id": access.dataset_id,
            "dataset_name": access.name,
            "replica_id": chosen.replica_id if chosen else "",
            "center_id": chosen.center_id if chosen else "",
            "locator": chosen.locator if chosen else "",
            "reason": access.replica_decision.reason,
            "alternatives": list(access.alternatives),
            "warnings": list(plan.validation.warnings),
        }

    from runtime.cross_dag.executor import submit_cross_dag_plan

    result = submit_cross_dag_plan(plan)

    from runtime.cross_dag.run_store import save_cross_dag_execution

    save_cross_dag_execution(
        process_id=result.process_id,
        plan_id=plan.plan_id,
        user_id=user_id,
        execution_center_id=result.execution_node_id,
        remote_grpc_target=result.remote_grpc_target,
        submit_status=result.status,
    )

    log.info(
        "cross dag submitted plan_id=%s center_id=%s process_id=%s",
        plan.plan_id,
        result.execution_node_id,
        result.process_id,
    )
    return {
        "plan_id": plan.plan_id,
        "mode": plan.mode,
        "execution_center_id": result.execution_node_id,
        "process_id": result.process_id,
        "status": result.status,
        "status_url": f"/api/piflow/v1/xdc/execution/{result.process_id}/status",
        "download_url": f"/api/piflow/v1/xdc/execution/{result.process_id}/download",
        "warnings": list(plan.validation.warnings),
    }


def execute_direct_session_plan(
    *,
    plan: CrossDagPlan,
    user_id: str,
) -> dict[str, Any]:
    """Submit a direct plan for the session workflow and expose one file result."""
    from runtime.cross_dag.direct_executor import submit_direct_access_plan
    from runtime.cross_dag.run_store import save_cross_dag_execution

    submission = submit_direct_access_plan(plan)
    result = submission.result
    _remember(plan)
    save_cross_dag_execution(
        process_id=result.process_id,
        plan_id=plan.plan_id,
        user_id=user_id,
        execution_center_id=result.execution_node_id,
        remote_grpc_target=result.remote_grpc_target,
        submit_status=result.status,
    )

    access = plan.direct_access
    decision = access.replica_decision if access is not None else None
    chosen = decision.chosen if decision is not None else None
    query = urlencode(
        {
            "result_node_id": submission.result_node_id,
            "result_output_name": submission.result_output_name,
        }
    )
    log.info(
        "cross dag direct run submitted plan_id=%s center_id=%s process_id=%s",
        plan.plan_id,
        result.execution_node_id,
        result.process_id,
    )
    return {
        "plan_id": plan.plan_id,
        "mode": plan.mode,
        "dataset_id": access.dataset_id if access is not None else "",
        "dataset_name": access.name if access is not None else "",
        "replica_id": chosen.replica_id if chosen is not None else "",
        "center_id": chosen.center_id if chosen is not None else "",
        "locator": chosen.locator if chosen is not None else "",
        "reason": decision.reason if decision is not None else "",
        "alternatives": list(access.alternatives) if access is not None else [],
        "execution_center_id": result.execution_node_id,
        "process_id": result.process_id,
        "status": result.status,
        "result_node_id": submission.result_node_id,
        "result_output_name": submission.result_output_name,
        "status_url": (
            f"/api/piflow/v1/xdc/execution/{result.process_id}/status?{query}"
        ),
        "download_url": (
            f"/api/piflow/v1/xdc/execution/{result.process_id}/download?{query}"
        ),
        "warnings": list(plan.validation.warnings),
    }


def get_cross_dag_execution_status(
    *,
    process_id: str,
    user_id: str,
    result_node_id: str = "",
    result_output_name: str = "",
) -> dict[str, Any]:
    """Query the root execution service and expose a frontend-safe status."""
    record = _require_cross_dag_execution(process_id=process_id, user_id=user_id)

    from piflow_engine.cn.piflow.remote.client import RemoteExecutionClient
    from runtime.cross_dag.run_store import update_cross_dag_execution_status

    client = RemoteExecutionClient(str(record["remote_grpc_target"]))
    try:
        response = client.get_run_status(process_id)
        status = str(response.status or "").strip().upper()
        message = str(response.message or "")
        update_cross_dag_execution_status(
            process_id,
            status=status,
            message=message,
        )

        result_file = None
        result_error = ""
        if status == "SUCCESS":
            try:
                meta = client.get_run_result_meta(
                    run_id=process_id,
                    result_node_id=result_node_id,
                    result_output_name=result_output_name,
                )
                result_file = {
                    "file_name": str(meta.file_name or ""),
                    "file_size": int(meta.file_size or 0),
                    "mime_type": str(meta.mime_type or "application/octet-stream"),
                    "download_url": _cross_dag_download_url(
                        process_id,
                        result_node_id=result_node_id,
                        result_output_name=result_output_name,
                    ),
                }
            except Exception as exc:
                # The run has succeeded even if its selected output is absent.
                # Keep status polling usable and report the result issue
                # separately instead of turning the whole request into 500.
                result_error = str(exc)
    finally:
        client.close()

    terminal = status in {"SUCCESS", "FAILED", "CANCELLED"}
    return {
        "plan_id": str(record["plan_id"]),
        "process_id": process_id,
        "execution_center_id": str(record["execution_center_id"]),
        "status": status,
        "message": message,
        "terminal": terminal,
        "downloadable": result_file is not None,
        "result_file": result_file,
        "result_error": result_error,
    }


def prepare_cross_dag_result_download(
    *,
    process_id: str,
    user_id: str,
    result_node_id: str = "",
    result_output_name: str = "",
) -> CrossDagResultDownload:
    """Download one remote result to an API-owned temporary file."""
    record = _require_cross_dag_execution(process_id=process_id, user_id=user_id)

    from piflow_engine.cn.piflow.remote.client import RemoteExecutionClient
    from runtime.cross_dag.run_store import update_cross_dag_execution_status

    client = RemoteExecutionClient(str(record["remote_grpc_target"]))
    target: Path | None = None
    try:
        response = client.get_run_status(process_id)
        status = str(response.status or "").strip().upper()
        message = str(response.message or "")
        update_cross_dag_execution_status(
            process_id,
            status=status,
            message=message,
        )
        if status != "SUCCESS":
            raise CrossDagExecutionNotReady(
                f"任务尚不可下载: process_id={process_id}, status={status or 'UNKNOWN'}"
            )

        meta = client.get_run_result_meta(
            run_id=process_id,
            result_node_id=result_node_id,
            result_output_name=result_output_name,
        )
        file_name = Path(str(meta.file_name or "result.bin")).name or "result.bin"
        download_dir = (resolve_workspace_root() / "temp" / "xdc_downloads").resolve()
        download_dir.mkdir(parents=True, exist_ok=True)
        target = (download_dir / f"{uuid.uuid4().hex}_{file_name}").resolve()
        target.relative_to(download_dir)

        client.download_result(
            run_id=process_id,
            result_node_id=result_node_id,
            result_output_name=result_output_name,
            target_path=target,
        )
        if not target.is_file():
            raise FileNotFoundError(f"下载结果文件未生成: {file_name}")
        expected_size = int(meta.file_size or 0)
        if expected_size and target.stat().st_size != expected_size:
            raise IOError(
                f"下载结果大小不一致: expected={expected_size}, actual={target.stat().st_size}"
            )
        return CrossDagResultDownload(
            path=target,
            file_name=file_name,
            media_type=str(meta.mime_type or "application/octet-stream"),
        )
    except Exception:
        if target is not None:
            target.unlink(missing_ok=True)
        raise
    finally:
        client.close()


def _require_cross_dag_execution(*, process_id: str, user_id: str) -> dict[str, Any]:
    from runtime.cross_dag.run_store import get_cross_dag_execution

    normalized_process_id = str(process_id or "").strip()
    if not normalized_process_id:
        raise CrossDagExecutionNotFound("process_id 不能为空")
    record = get_cross_dag_execution(normalized_process_id)
    if record is None:
        raise CrossDagExecutionNotFound(
            f"跨域执行记录不存在: {normalized_process_id}"
        )
    if str(record.get("user_id") or "") != str(user_id or ""):
        raise PermissionError("无权访问该跨域执行记录")
    return record


def _cross_dag_download_url(
    process_id: str,
    *,
    result_node_id: str = "",
    result_output_name: str = "",
) -> str:
    base = f"/api/piflow/v1/xdc/execution/{process_id}/download"
    query = {
        key: value
        for key, value in {
            "result_node_id": result_node_id,
            "result_output_name": result_output_name,
        }.items()
        if value
    }
    return f"{base}?{urlencode(query)}" if query else base


async def stream_cross_dag_plan(
    *, user_request: str, user_id: str, detail: bool = False
) -> Any:
    """SSE 版规划。逐阶段推摘要，done 事件给最终方案。

    必须走 service 层而不是直接用 runtime 的生成器：规划完要把 plan 记进缓存，
    否则前端从 done 事件里拿到的 plan_id，回头 GET /xdc/plan/{id} 是 404，
    POST /xdc/execute 也用不了 —— 步骤条能跑完，却什么都点不下去。
    """
    from runtime.cross_dag.engine import stream_plan_cross_dag

    plan_id = f"xdc-{uuid.uuid4().hex[:12]}"
    async for event in stream_plan_cross_dag(
        user_request, detail=detail, plan_id=plan_id, on_plan=_remember
    ):
        yield event


async def stream_cross_dag_pre_bind_plan(
    *,
    user_request: str,
    user_id: str,
    detail: bool = False,
) -> AsyncIterator[dict[str, Any]]:
    """Stream intent through logical expansion and cache the pre-bind result."""
    from runtime.cross_dag.plan_view import stage_brief

    plan_id = f"xdc-{uuid.uuid4().hex[:12]}"
    events: list[dict[str, Any]] = []
    result: list[CrossDagPreBindPlan] = []

    def collect(stage: str, payload: dict[str, Any]) -> None:
        if detail:
            events.append({"type": "stage", "stage": stage, **payload})
        else:
            events.append({"type": "stage", **stage_brief(stage, payload)})

    def run() -> None:
        pre_bind = plan_cross_dag_pre_bind(
            user_request,
            plan_id=plan_id,
            on_stage=collect,
        )
        _remember_pre_bind(pre_bind, user_id=user_id)
        result.append(pre_bind)

    yield {"type": "status", "stage": "started"}
    try:
        async for event in _stream_worker_events(run, events):
            yield event
    except Exception as exc:
        yield {"type": "error", "message": str(exc)}
        return

    yield {
        "type": "done",
        "result": _summarize_pre_bind(result[0], detail=detail),
    }


async def stream_bind_and_execute_cross_dag_pre_bind(
    *,
    plan_id: str,
    user_id: str,
    detail: bool = False,
    selected_dataset_id: str | None = None,
) -> AsyncIterator[dict[str, Any]]:
    """Stream replica binding through submission for a cached pre-bind plan."""
    from runtime.cross_dag.plan_view import stage_brief

    events: list[dict[str, Any]] = []
    result: list[tuple[CrossDagPlan, dict[str, Any]]] = []
    pre_bind: list[CrossDagPreBindPlan] = []
    candidates_emitted = False

    def collect(stage: str, payload: dict[str, Any]) -> None:
        nonlocal candidates_emitted

        if detail:
            stage_event = {"type": "stage", "stage": stage, **payload}
        else:
            brief = stage_brief(stage, payload)
            if stage == "submit" and payload.get("status") == "finished":
                process_id = str(payload.get("process_id") or "")
                brief["summary"] = (
                    f"任务已提交 · {process_id}"
                    if process_id
                    else "直接访问方案已确定，无需提交 DAG"
                )
            stage_event = {"type": "stage", **brief}

        if (
            stage in {"bind", "access"}
            and payload.get("status") == "started"
            and pre_bind
            and not candidates_emitted
        ):
            events.append(stage_event)
            events.extend(
                _replica_candidate_events(
                    pre_bind[0],
                    detail=detail,
                    dataset_id=(
                        selected_dataset_id
                        if pre_bind[0].mode == MODE_DIRECT
                        else None
                    ),
                )
            )
            candidates_emitted = True
            return

        if stage in {"bind", "access"} and payload.get("status") == "finished":
            events.extend(
                _replica_selection_events(
                    pre_bind[0],
                    stage=stage,
                    payload=payload,
                    detail=detail,
                )
            )
        events.append(stage_event)

    def run() -> None:
        owned = _get_owned_pre_bind(plan_id=plan_id, user_id=user_id)
        pre_bind.append(owned)
        if owned.mode == MODE_DIRECT:
            finalized = _finalize_and_execute_pre_bind(
                owned,
                user_id=user_id,
                on_stage=collect,
                selected_dataset_id=selected_dataset_id,
            )
        else:
            finalized = _finalize_and_execute_pre_bind(
                owned,
                user_id=user_id,
                on_stage=collect,
            )
        result.append(finalized)

    yield {"type": "status", "stage": "started"}
    try:
        async for event in _stream_worker_events(run, events):
            yield event
    except Exception as exc:
        yield {"type": "error", "message": str(exc)}
        return

    plan, execution = result[0]
    yield {
        "type": "done",
        "result": {
            "plan": _summarize(plan, detail=detail),
            "execution": execution,
        },
    }


async def _stream_worker_events(
    worker: Callable[[], None],
    events: list[dict[str, Any]],
) -> AsyncIterator[dict[str, Any]]:
    """Run blocking planning work in a thread while draining emitted events."""
    import asyncio

    task = asyncio.get_running_loop().run_in_executor(None, worker)
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


def _replica_candidate_events(
    pre_bind: CrossDagPreBindPlan,
    *,
    detail: bool,
    dataset_id: str | None = None,
) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    datasets = list(pre_bind.intent.datasets)
    normalized_dataset_id = str(dataset_id or "").strip()
    if normalized_dataset_id:
        resolved = _resolve_pre_bind_dataset(pre_bind, normalized_dataset_id)
        datasets = [resolved] if resolved is not None else []

    for dataset in datasets:
        replicas = list(getattr(dataset, "replicas", ()) or ())
        if not replicas:
            continue
        candidates = []
        for replica in replicas:
            item: dict[str, Any] = {
                "replica_id": replica.replica_id,
                "center_id": getattr(replica, "center_id", "")
                or getattr(replica, "source_ip", ""),
                "status": replica.status,
            }
            if detail:
                item["metrics"] = dict(replica.metrics)
            candidates.append(item)
        events.append(
            {
                "type": "replica",
                "stage": "bind",
                "status": "evaluating",
                "dataset_id": dataset.dataset_id,
                "dataset_name": dataset.name,
                "candidate_count": len(candidates),
                "candidates": candidates,
            }
        )
    return events


def _replica_selection_events(
    pre_bind: CrossDagPreBindPlan,
    *,
    stage: str,
    payload: dict[str, Any],
    detail: bool,
) -> list[dict[str, Any]]:
    decisions = list(payload.get("replica_decisions") or [])
    if stage == "access":
        direct_access = payload.get("direct_access") or {}
        direct_decision = direct_access.get("replica_decision")
        decisions = [direct_decision] if isinstance(direct_decision, dict) else []

    events: list[dict[str, Any]] = []
    for decision in decisions:
        if not isinstance(decision, dict):
            continue
        chosen = decision.get("chosen") or {}
        if not chosen:
            continue
        dataset_id = str(decision.get("dataset_id") or "")
        dataset = _resolve_pre_bind_dataset(pre_bind, dataset_id)
        replica_id = str(chosen.get("replica_id") or "")
        reason = str(decision.get("reason") or "")
        replicas = list(getattr(dataset, "replicas", ()) or ()) if dataset else []
        event: dict[str, Any] = {
            "type": "replica",
            "stage": "bind",
            "status": "selected",
            "dataset_id": dataset_id,
            "dataset_name": dataset.name if dataset else "",
            "node_id": str(decision.get("node_id") or ""),
            "candidate_count": len(replicas),
            "chosen": {
                "replica_id": replica_id,
                "center_id": str(chosen.get("center_id") or ""),
            },
            "summary": _replica_choice_summary(
                replica_id=replica_id,
                reason=reason,
                candidate_count=len(replicas),
            ),
            # This is the one stable, human-readable scheduling basis that the
            # ordinary frontend needs. Scores remain opt-in diagnostic data.
            "reason": reason,
        }
        if detail:
            event["selection_detail"] = {
                "preferred_center_id": str(
                    decision.get("preferred_center_id") or ""
                ),
                "scores": list(decision.get("scores") or []),
                "rejects": list(decision.get("rejects") or []),
            }
        events.append(event)
    return events


def _resolve_pre_bind_dataset(
    pre_bind: CrossDagPreBindPlan,
    dataset_id: str,
) -> Any | None:
    """Resolve an intent-selected or catalog-discovered Direct candidate."""
    normalized = str(dataset_id or "").strip()
    for dataset in pre_bind.intent.datasets:
        if dataset.dataset_id == normalized:
            return dataset
    if not normalized:
        return None
    return get_registry().get_dataset(normalized)


def _replica_choice_summary(
    *, replica_id: str, reason: str, candidate_count: int
) -> str:
    """Return one short sentence for the ordinary replica-selection timeline."""
    if candidate_count == 1:
        basis = "它是当前唯一可用的副本"
    else:
        clauses = [
            item.strip().rstrip("。.")
            for item in reason.replace("\n", " ").replace(";", "；").split("；")
            if item.strip()
        ]
        basis = next(
            (
                item
                for keyword in ("免跨", "一致", "就近", "优势项", "总分")
                for item in clauses
                if keyword in item
            ),
            "综合位置与资源指标后得分最高",
        )
    return f"选择副本 {replica_id}，因为{basis}。"


def list_cross_dag_context() -> dict[str, Any]:
    """中心清单 + 数据集清单，供前端展示和排障。"""
    config = get_cross_dc_config()
    registry = refresh_registry(get_registry())
    config = resolve_cross_dc_config(config, registry)
    return {
        "local_center_id": config.local_center_id,
        "default_center_id": config.default_center_id,
        "centers": [
            {
                "center_id": center.center_id,
                "center_name": center.center_name,
                # grpc_endpoint 不外发：那是中心之间互调的内部地址，
                # 浏览器用不上，暴露出去等于把内网拓扑贴在页面上
            }
            for center in config.centers.values()
        ],
        "datasets": [item.to_json() for item in registry.list_datasets()],
    }


def _summarize(plan: CrossDagPlan, *, detail: bool = False) -> dict[str, Any]:
    """对外只给前端渲染需要的结构。完整数据（嵌套 DSL、打分表、段图）走 detail。"""
    from runtime.cross_dag.plan_view import build_plan_view

    config = resolve_cross_dc_config(get_cross_dc_config(), get_registry())
    return build_plan_view(plan, detail=detail, config=config)


def _summarize_direct_session(
    plan: CrossDagPlan,
    *,
    detail: bool = False,
) -> dict[str, Any]:
    """Direct-only session projection with unified `dag` and `sources` fields."""
    from runtime.cross_dag.plan_view import build_direct_execution_plan_view

    config = resolve_cross_dc_config(get_cross_dc_config(), get_registry())
    return build_direct_execution_plan_view(plan, detail=detail, config=config)


def _summarize_pre_bind(
    pre_bind: CrossDagPreBindPlan,
    *,
    detail: bool = False,
) -> dict[str, Any]:
    """Frontend view before replica selection; never expose a chosen replica."""
    config = resolve_cross_dc_config(get_cross_dc_config(), get_registry())

    def center_name(center_id: str) -> str:
        center = config.centers.get(center_id)
        return center.center_name if center else center_id

    datasets = []
    for dataset in pre_bind.intent.datasets:
        datasets.append(
            {
                "dataset_id": dataset.dataset_id,
                "name": dataset.name,
                "facets": {key: list(values) for key, values in dataset.facets.items()},
                "replicas": [
                    {
                        "replica_id": replica.replica_id,
                        "center_id": replica.center_id,
                        "center_name": center_name(replica.center_id),
                        "status": replica.status,
                        "metrics": dict(replica.metrics),
                    }
                    for replica in dataset.replicas
                ],
            }
        )

    logical = pre_bind.logical_dag
    view: dict[str, Any] = {
        "plan_id": pre_bind.plan_id,
        "stage": "pre_bind",
        "binding_status": "PENDING",
        "mode": pre_bind.mode,
        "conclusion": pre_bind.satisfaction.reason,
        "can_continue": (
            pre_bind.mode != MODE_UNAVAILABLE and pre_bind.validation.ok
        ),
        "validation": pre_bind.validation.to_json(),
        "requirement": {
            "goal": pre_bind.intent.goal,
            "user_request": pre_bind.intent.user_request,
            "operations": list(pre_bind.intent.operations),
            "assumptions": list(pre_bind.intent.assumptions),
            "unresolved": list(pre_bind.intent.unresolved),
        },
        "datasets": datasets,
        "logical_dag": {
            "task_name": logical.task_name,
            "description": logical.description,
            "nodes": [
                {
                    "id": node.node_id,
                    "name": node.node_name,
                    "skill_name": node.skill_name or node.skill_id,
                }
                for node in logical.nodes
            ],
            "edges": [
                {
                    "from": binding.from_node_id,
                    "from_param": binding.from_param_name,
                    "to": binding.to_node_id,
                    "to_param": binding.to_param_name,
                }
                for binding in logical.bindings
            ],
        },
        "next_action": {
            "method": "POST",
            "url": "/api/piflow/v1/xdc/bind-and-execute",
            "body": {"plan_id": pre_bind.plan_id},
        },
    }
    if pre_bind.mode == MODE_DIRECT:
        view["dataset_selection"] = _direct_dataset_selection_view(pre_bind)
        view["next_action"]["body"]["selected_dataset_id"] = None
    if detail:
        view["detail"] = {
            "intent": pre_bind.intent.to_json(),
            "satisfaction": pre_bind.satisfaction.to_json(),
            "planning_json": pre_bind.planning_json,
            "logical_dag": pre_bind.logical_dag.to_json(),
        }
    return view


def _direct_dataset_selection_view(
    pre_bind: CrossDagPreBindPlan,
) -> dict[str, Any]:
    """Return every full-match dataset without selecting one for the user."""
    registry = get_registry()
    matches = list(pre_bind.satisfaction.full_matches)
    ordered = [item for item in matches if item.selected] + [
        item for item in matches if not item.selected
    ]
    intent_by_id = {
        dataset.dataset_id: dataset for dataset in pre_bind.intent.datasets
    }
    candidates: list[dict[str, Any]] = []
    for index, coverage in enumerate(ordered):
        record = registry.get_dataset(coverage.dataset_id)
        dataset = intent_by_id.get(coverage.dataset_id)
        facets = (
            {str(key): list(values) for key, values in record.facets.items()}
            if record is not None
            else {
                str(key): list(values)
                for key, values in (dataset.facets if dataset else {}).items()
            }
        )
        replicas = list(
            (record.replicas if record is not None else dataset.replicas if dataset else ())
        )
        candidates.append(
            {
                "dataset_id": coverage.dataset_id,
                "name": coverage.name
                or (record.name if record is not None else dataset.name if dataset else ""),
                "description": record.description if record is not None else "",
                "tags": list(record.tags) if record is not None else [],
                "facets": facets,
                "replica_count": len(replicas),
                "available_replica_count": sum(
                    1
                    for replica in replicas
                    if str(getattr(replica, "status", "")).upper() == "AVAILABLE"
                ),
                "recommended": index == 0,
                "intent_selected": coverage.selected,
                "coverage": {
                    "full_match": coverage.full_match,
                    "matched_count": sum(
                        len(facet.covered) for facet in coverage.facets
                    ),
                    "required_count": sum(
                        len(facet.required) for facet in coverage.facets
                    ),
                    "facets": [facet.to_json() for facet in coverage.facets],
                },
            }
        )
    return {
        "required": True,
        "selected_dataset_id": None,
        "candidate_count": len(candidates),
        "candidates": candidates,
    }


def _remember(plan: CrossDagPlan) -> None:
    with _CACHE_LOCK:
        if len(_PLAN_CACHE) >= _CACHE_LIMIT:
            for stale in list(_PLAN_CACHE)[: _CACHE_LIMIT // 2]:
                _PLAN_CACHE.pop(stale, None)
        _PLAN_CACHE[plan.plan_id] = plan


def _remember_pre_bind(pre_bind: CrossDagPreBindPlan, *, user_id: str) -> None:
    with _CACHE_LOCK:
        if len(_PRE_BIND_CACHE) >= _CACHE_LIMIT:
            for stale in list(_PRE_BIND_CACHE)[: _CACHE_LIMIT // 2]:
                _PRE_BIND_CACHE.pop(stale, None)
        _PRE_BIND_CACHE[pre_bind.plan_id] = (str(user_id or ""), pre_bind)


def _get_owned_pre_bind(*, plan_id: str, user_id: str) -> CrossDagPreBindPlan:
    with _CACHE_LOCK:
        stored = _PRE_BIND_CACHE.get(plan_id)
    if stored is None:
        raise CrossDagError(f"预绑定计划不存在或已过期: {plan_id}")
    owner_id, pre_bind = stored
    if owner_id != str(user_id or ""):
        raise PermissionError("无权访问该预绑定计划")
    return pre_bind
