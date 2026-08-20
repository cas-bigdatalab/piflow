from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from runtime.remote_dag_scheduler import RemoteNodeResource
from runtime.remote_dag_scheduler import schedule_frontend_dag


@dataclass(frozen=True)
class CrossDomainSubmitResult:
    process_id: str
    status: str
    execution_node_id: str
    remote_grpc_target: str
    dag_definition: dict[str, Any]


def create_remote_execution_client(remote_grpc_target: str):
    from piflow_engine.cn.piflow.remote.client import RemoteExecutionClient

    return RemoteExecutionClient(remote_grpc_target)


def submit_cross_domain_dag(
    definition_json: dict[str, Any],
    *,
    remote_grpc_target: str,
    execution_node_id: str | None = None,
    random_seed: int | None = None,
    workspace_root: str | Path | None = None,
    user_id: str | None = None,
    python_home: str | None = None,
) -> CrossDomainSubmitResult:
    remote_target = str(remote_grpc_target or "").strip()
    if not remote_target:
        raise ValueError("remote_grpc_target must not be empty")

    resource_resolver = _build_remote_resource_resolver()
    plan = schedule_frontend_dag(
        definition_json,
        execution_node_id=execution_node_id,
        random_seed=random_seed,
        resource_resolver=resource_resolver,
    )

    return submit_remote_root_dag(
        plan.dag_definition,
        remote_grpc_target=remote_target,
        execution_node_id=plan.execution_node_id,
    )


def submit_remote_root_dag(
    definition_json: dict[str, Any],
    *,
    remote_grpc_target: str,
    execution_node_id: str = "",
) -> CrossDomainSubmitResult:
    """提交已经完成分段/嵌套的根 DAG，不再做二次调度。

    ``submit_cross_domain_dag`` 保留给旧的平面 DAG demo；cross_dag 编译器已经完成
    全图绑定和递归嵌套，必须走本函数，否则再次切图会破坏已生成的边界。
    """
    remote_target = str(remote_grpc_target or "").strip()
    if not remote_target:
        raise ValueError("remote_grpc_target must not be empty")
    if not isinstance(definition_json, dict):
        raise TypeError("definition_json must be a dict")

    client = create_remote_execution_client(remote_target)
    try:
        response = client.submit_remote_root_dag(
            json.dumps(definition_json, ensure_ascii=False)
        )
    finally:
        client.close()

    return CrossDomainSubmitResult(
        process_id=str(response.run_id),
        status=str(response.status),
        execution_node_id=str(execution_node_id or ""),
        remote_grpc_target=remote_target,
        dag_definition=definition_json,
    )


def _build_remote_resource_resolver():
    resource_cache: dict[str, RemoteNodeResource] = {}

    def resolve(node: dict[str, Any]) -> RemoteNodeResource:
        from runtime.remote_dag_scheduler import _read_remote_node_resource

        declared = _read_remote_node_resource(node)
        node_id = declared.node_id
        remote_target = declared.remote_grpc_target
        if not remote_target:
            raise ValueError(f"remote source {node.get('node_id')} has no gRPC target")
        cached = resource_cache.get(remote_target)
        if cached is not None:
            return RemoteNodeResource(
                node_id=node_id,
                cpu_cores=cached.cpu_cores,
                memory_gb=cached.memory_gb,
                free_disk_gb=cached.free_disk_gb,
                remote_grpc_target=remote_target,
            )

        resolved = RemoteNodeResource(
            node_id=node_id,
            cpu_cores=declared.cpu_cores,
            memory_gb=declared.memory_gb,
            free_disk_gb=declared.free_disk_gb,
            remote_grpc_target=remote_target,
        )
        resource_cache[remote_target] = resolved
        return resolved

    return resolve
