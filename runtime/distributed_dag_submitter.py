from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Collection

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
    resource_resolver: Callable[[dict[str, Any]], RemoteNodeResource] | None = None,
    remote_source_node_ids: Collection[str] | None = None,
) -> CrossDomainSubmitResult:
    remote_target = str(remote_grpc_target or "").strip()
    if not remote_target:
        raise ValueError("remote_grpc_target must not be empty")

    resolved_resource_resolver = resource_resolver or _build_remote_resource_resolver()
    plan = schedule_frontend_dag(
        definition_json,
        execution_node_id=execution_node_id,
        random_seed=random_seed,
        resource_resolver=resolved_resource_resolver,
        remote_source_node_ids=remote_source_node_ids,
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
        from runtime.remote_dag_scheduler import CORPUS_DATASET_SOURCE_BUNDLE
        from runtime.remote_dag_scheduler import _read_dataset_id
        from runtime.remote_dag_scheduler import _read_remote_grpc_target
        from runtime.remote_dag_scheduler import _require_remote_node_id

        skill = node.get("skill") or {}
        skill_id = str(skill.get("skill_id", "") or "")
        skill_name = str(skill.get("skill_name", "") or "")

        if skill_id == CORPUS_DATASET_SOURCE_BUNDLE or skill_name == "corpus_dataset_source_stop":
            dataset_id = _read_dataset_id(node)
            cached = resource_cache.get(dataset_id)
            if cached is not None:
                return cached

            from services.corpus_connector_service import get_dataset_connector_detail_with_resource

            resolved = get_dataset_connector_detail_with_resource(dataset_id)
            resource = resolved.get("resource") or {}
            remote_target = str(resolved.get("remote_grpc_target", "") or "").strip()
            connector_id = str(resolved.get("dataset", {}).get("connectorId", "") or "").strip()
            if not connector_id:
                connector_id = str((resolved.get("connector") or {}).get("connectorId", "") or "").strip()
            if not connector_id:
                raise ValueError(f"dataset_id {dataset_id} does not resolve to a connectorId")
            if not remote_target:
                raise ValueError(f"dataset_id {dataset_id} does not resolve to a remote_grpc_target")

            resolved_resource = RemoteNodeResource(
                node_id=connector_id,
                cpu_cores=float(resource.get("cpu_cores", 0.0) or 0.0),
                memory_gb=float(resource.get("memory_gb", 0.0) or 0.0),
                free_disk_gb=float(resource.get("free_disk_gb", 0.0) or 0.0),
                remote_grpc_target=remote_target,
            )
            resource_cache[dataset_id] = resolved_resource
            return resolved_resource

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
            remote_grpc_target=remote_target,
        )
        resource_cache[remote_target] = resolved
        return resolved

    return resolve
