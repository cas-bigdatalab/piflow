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

    # The caller has already decided to use remote submission. This submitter
    # therefore skips local-node checks and directly hands the scheduled root
    # DAG to the chosen remote client endpoint.
    client = create_remote_execution_client(remote_target)
    try:
        response = client.submit_remote_root_dag(
            json.dumps(plan.dag_definition, ensure_ascii=False)
        )
    finally:
        client.close()

    return CrossDomainSubmitResult(
        process_id=str(response.run_id),
        status=str(response.status),
        execution_node_id=plan.execution_node_id,
        remote_grpc_target=remote_target,
        dag_definition=plan.dag_definition,
    )


def _build_remote_resource_resolver():
    resource_cache: dict[str, RemoteNodeResource] = {}

    def resolve(node: dict[str, Any]) -> RemoteNodeResource:
        from runtime.remote_dag_scheduler import _read_remote_grpc_target
        from runtime.remote_dag_scheduler import _require_remote_node_id

        node_id = _require_remote_node_id(node)
        remote_target = _read_remote_grpc_target(node)
        cached = resource_cache.get(remote_target)
        if cached is not None:
            return RemoteNodeResource(
                node_id=node_id,
                cpu_cores=cached.cpu_cores,
                memory_gb=cached.memory_gb,
                free_disk_gb=cached.free_disk_gb,
            )

        client = create_remote_execution_client(remote_target)
        try:
            resource = client.get_server_resource()
        finally:
            client.close()

        resolved = RemoteNodeResource(
            node_id=node_id,
            cpu_cores=float(resource.cpu_cores),
            memory_gb=float(resource.memory_gb),
            free_disk_gb=float(resource.free_disk_gb),
        )
        resource_cache[remote_target] = resolved
        return resolved

    return resolve
