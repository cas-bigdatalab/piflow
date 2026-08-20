"""跨域计划与远程执行引擎之间的交接层。"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Callable

from runtime.distributed_dag_submitter import (
    CrossDomainSubmitResult,
    submit_cross_domain_dag,
)
from runtime.remote_dag_scheduler import RemoteNodeResource

from .schema import MODE_COMPOSITION, CrossDagError, CrossDagPlan

ClientFactory = Callable[[str], Any]


def submit_cross_dag_plan(plan: CrossDagPlan) -> CrossDomainSubmitResult:
    """把执行引擎格式的平铺 DAG 交给跨域调度/执行入口。"""
    if plan.mode != MODE_COMPOSITION:
        raise CrossDagError(f"{plan.mode} 计划没有可提交的 DAG")
    if not plan.validation.ok:
        raise CrossDagError(
            "计划未通过校验，拒绝执行:\n" + "\n".join(plan.validation.errors)
        )
    if not plan.execution_dsl:
        raise CrossDagError("跨域计划没有生成 execution_dsl")
    if not plan.execution_center_id:
        raise CrossDagError("跨域计划没有确定根执行位置")
    if not plan.execution_grpc_endpoint:
        raise CrossDagError(
            f"根执行位置 {plan.execution_center_id} 没有可用的 gRPC 地址"
        )

    return submit_cross_domain_dag(
        plan.execution_dsl,
        remote_grpc_target=plan.execution_grpc_endpoint,
        execution_node_id=plan.execution_center_id,
        resource_resolver=_plan_resource_resolver(plan),
        remote_source_node_ids=plan.logical_dag.source_node_ids(),
    )


def _plan_resource_resolver(
    plan: CrossDagPlan,
) -> Callable[[dict[str, Any]], RemoteNodeResource]:
    decisions = {
        decision.node_id: decision
        for decision in plan.bind_result.replica_decisions
        if decision.node_id and decision.chosen is not None
    }

    def resolve(node: dict[str, Any]) -> RemoteNodeResource:
        node_id = str(node.get("node_id", "") or "")
        center_id = str(plan.bind_result.center_of.get(node_id, "") or "")
        if not center_id:
            raise CrossDagError(f"数据源节点 {node_id} 没有绑定执行位置")

        endpoint = str(plan.center_endpoints.get(center_id, "") or "")
        if not endpoint:
            raise CrossDagError(
                f"数据源节点 {node_id} 的执行位置 {center_id} 没有 gRPC 地址"
            )

        chosen = getattr(decisions.get(node_id), "chosen", None)
        metrics = chosen.metrics if chosen is not None else {}
        return RemoteNodeResource(
            node_id=center_id,
            cpu_cores=float(metrics.get("cpu_cores", 0.0) or 0.0),
            memory_gb=float(metrics.get("memory_gb", 0.0) or 0.0),
            free_disk_gb=float(metrics.get("free_disk_gb", 0.0) or 0.0),
            remote_grpc_target=endpoint,
        )

    return resolve


def wait_for_cross_dag_run(
    submission: CrossDomainSubmitResult,
    *,
    poll_interval_seconds: float = 1.0,
    timeout_seconds: float | None = None,
    client_factory: ClientFactory | None = None,
) -> Any:
    """等待远端根任务结束并返回最后一次状态响应。"""
    if poll_interval_seconds <= 0:
        raise ValueError("poll_interval_seconds must be positive")
    if timeout_seconds is not None and timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive when provided")

    factory = client_factory or _client_factory
    client = factory(submission.remote_grpc_target)
    started = time.monotonic()
    try:
        while True:
            response = client.get_run_status(submission.process_id)
            status = str(response.status or "").upper()
            if status == "SUCCESS":
                return response
            if status in {"FAILED", "CANCELLED"}:
                raise CrossDagError(
                    f"远端任务 {submission.process_id} 执行失败: "
                    f"{status} {getattr(response, 'message', '')}"
                )
            if timeout_seconds is not None and time.monotonic() - started >= timeout_seconds:
                raise TimeoutError(
                    f"等待远端任务 {submission.process_id} 超时（{timeout_seconds}s）"
                )
            time.sleep(poll_interval_seconds)
    finally:
        client.close()


def download_cross_dag_result(
    submission: CrossDomainSubmitResult,
    target_path: str | Path,
    *,
    result_node_id: str = "",
    result_output_name: str = "",
    client_factory: ClientFactory | None = None,
) -> Path:
    """下载远端根任务产物。空节点/端口表示让执行引擎选择最终产物。"""
    target = Path(target_path).expanduser().resolve()
    factory = client_factory or _client_factory
    client = factory(submission.remote_grpc_target)
    try:
        downloaded = client.download_result(
            run_id=submission.process_id,
            result_node_id=result_node_id,
            result_output_name=result_output_name,
            target_path=target,
        )
    finally:
        client.close()
    return Path(downloaded).resolve()


def _client_factory(remote_grpc_target: str) -> Any:
    from piflow_engine.cn.piflow.remote.client import RemoteExecutionClient

    return RemoteExecutionClient(remote_grpc_target)
