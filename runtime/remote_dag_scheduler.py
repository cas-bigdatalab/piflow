from __future__ import annotations

import copy
import json
import random
from dataclasses import dataclass
from typing import Any, Callable


REMOTE_SOURCE_BUNDLE = (
    "piflow_engine.cn.piflow.engine.local.remote_source_stop.RemoteSourceStop"
)
CORPUS_DATASET_SOURCE_BUNDLE = (
    "piflow_engine.cn.piflow.engine.local.corpus_dataset_source_stop.CorpusDatasetSourceStop"
)
REMOTE_SUBDAG_SOURCE_BUNDLE = (
    "piflow_engine.cn.piflow.engine.local.remote_subdag_source_stop.RemoteSubDagSourceStop"
)


@dataclass(frozen=True)
class ScheduledDagPlan:
    execution_node_id: str
    dag_definition: dict[str, Any]


@dataclass(frozen=True)
class RemoteNodeResource:
    node_id: str
    cpu_cores: float
    memory_gb: float
    free_disk_gb: float
    remote_grpc_target: str = ""


def schedule_frontend_dag(
    dag_definition: dict[str, Any],
    *,
    execution_node_id: str | None = None,
    random_seed: int | None = None,
    resource_resolver: Callable[[dict[str, Any]], RemoteNodeResource] | None = None,
) -> ScheduledDagPlan:
    definition = copy.deepcopy(dag_definition)
    nodes = definition.get("nodes", []) or []
    edges = definition.get("edges", []) or []
    bindings = definition.get("bindings", []) or []

    remote_sources = [
        node for node in nodes if _is_remote_source(node)
    ]
    if not remote_sources:
        raise ValueError("dag contains no supported remote source nodes")

    resolver = resource_resolver or _read_remote_node_resource
    source_resources = [
        (node, resolver(node))
        for node in remote_sources
    ]
    candidate_resources = [resource for _, resource in source_resources]
    chosen_node_id = execution_node_id or _choose_execution_node_id(
        candidate_resources,
        random_seed=random_seed,
    )

    incoming: dict[str, set[str]] = {node["node_id"]: set() for node in nodes}
    outgoing: dict[str, set[str]] = {node["node_id"]: set() for node in nodes}
    for edge in edges:
        from_id = str(edge.get("from_node_id", ""))
        to_id = str(edge.get("to_node_id", ""))
        if from_id and to_id:
            outgoing.setdefault(from_id, set()).add(to_id)
            incoming.setdefault(to_id, set()).add(from_id)

    nodes_to_remove: set[str] = set()
    added_nodes: list[dict[str, Any]] = []
    added_edges: list[dict[str, Any]] = []
    added_bindings: list[dict[str, Any]] = []

    for source, source_resource in source_resources:
        # CorpusDatasetSourceStop 只声明 dataset_id；它的运行节点由注册表解析得到，
        # 不要求 DAG 再重复携带一个容易过期的 node_id。
        source_runtime_node_id = source_resource.node_id
        if source_runtime_node_id == chosen_node_id:
            continue

        branch_node_ids = _collect_remote_branch(
            source_node_id=str(source["node_id"]),
            incoming=incoming,
            outgoing=outgoing,
        )
        nodes_to_remove.update(branch_node_ids)

        subdag = _build_subdag(
            definition=definition,
            branch_node_ids=branch_node_ids,
        )
        synthetic_node = _build_remote_subdag_source_node(
            source_runtime_node_id=source_runtime_node_id,
            source_remote_grpc_target=source_resource.remote_grpc_target,
            subdag_definition=subdag,
            source_node=source,
        )
        added_nodes.append(synthetic_node)

        for binding in bindings:
            from_node_id = str(binding.get("from_node_id", ""))
            to_node_id = str(binding.get("to_node_id", ""))
            if from_node_id in branch_node_ids and to_node_id not in branch_node_ids:
                added_bindings.append(
                    {
                        **binding,
                        "binding_id": f"binding-{synthetic_node['node_id']}-{to_node_id}-{binding.get('to_param_name', 'input')}",
                        "from_node_id": synthetic_node["node_id"],
                        "from_param_name": "output",
                    }
                )
        for edge in edges:
            from_node_id = str(edge.get("from_node_id", ""))
            to_node_id = str(edge.get("to_node_id", ""))
            if from_node_id in branch_node_ids and to_node_id not in branch_node_ids:
                added_edges.append(
                    {
                        **edge,
                        "edge_id": f"edge-{synthetic_node['node_id']}-{to_node_id}",
                        "from_node_id": synthetic_node["node_id"],
                    }
                )

    if not nodes_to_remove:
        return ScheduledDagPlan(execution_node_id=chosen_node_id, dag_definition=definition)

    definition["nodes"] = [
        node for node in nodes if node["node_id"] not in nodes_to_remove
    ] + added_nodes
    definition["edges"] = [
        edge
        for edge in edges
        if str(edge.get("from_node_id", "")) not in nodes_to_remove
        and str(edge.get("to_node_id", "")) not in nodes_to_remove
    ] + added_edges
    definition["bindings"] = [
        binding
        for binding in bindings
        if str(binding.get("from_node_id", "")) not in nodes_to_remove
        and str(binding.get("to_node_id", "")) not in nodes_to_remove
    ] + added_bindings

    return ScheduledDagPlan(execution_node_id=chosen_node_id, dag_definition=definition)


def _collect_remote_branch(
    *,
    source_node_id: str,
    incoming: dict[str, set[str]],
    outgoing: dict[str, set[str]],
) -> set[str]:
    branch: set[str] = {source_node_id}
    queue: list[str] = [source_node_id]

    while queue:
        current = queue.pop(0)
        for successor in sorted(outgoing.get(current, set())):
            predecessor_ids = incoming.get(successor, set())
            if predecessor_ids and predecessor_ids.issubset(branch):
                if successor not in branch:
                    branch.add(successor)
                    queue.append(successor)
    return branch


def _build_subdag(
    *,
    definition: dict[str, Any],
    branch_node_ids: set[str],
) -> dict[str, Any]:
    subdag = copy.deepcopy(definition)
    subdag["nodes"] = [
        node for node in subdag.get("nodes", []) if node["node_id"] in branch_node_ids
    ]
    subdag["edges"] = [
        edge
        for edge in subdag.get("edges", [])
        if str(edge.get("from_node_id", "")) in branch_node_ids
        and str(edge.get("to_node_id", "")) in branch_node_ids
    ]
    subdag["bindings"] = [
        binding
        for binding in subdag.get("bindings", [])
        if str(binding.get("from_node_id", "")) in branch_node_ids
        and str(binding.get("to_node_id", "")) in branch_node_ids
    ]
    return subdag


def _build_remote_subdag_source_node(
    *,
    source_runtime_node_id: str,
    source_remote_grpc_target: str,
    subdag_definition: dict[str, Any],
    source_node: dict[str, Any],
) -> dict[str, Any]:
    source_node_id = str(source_node["node_id"])
    return {
        "node_id": f"remote-subdag-source-{source_node_id}",
        "node_name": f"Remote subdag source for {source_node.get('node_name', source_node_id)}",
        "node_type": "synthetic_remote_source",
        "position": copy.deepcopy(source_node.get("position", {"x": 0, "y": 0})),
        "icon_path": source_node.get("icon_path", ""),
        "skill": {
            "skill_id": REMOTE_SUBDAG_SOURCE_BUNDLE,
            "skill_name": "remoteSubDagSourceNode",
            "version": "1.0.0",
        },
        "input_params": [
            _manual_param("remote_grpc_target", source_remote_grpc_target),
            _manual_param("subdag_definition_json", json.dumps(subdag_definition, ensure_ascii=False)),
        ],
        "out_params": [
            {
                "param_name": "output",
                "param_type": "file_artifact",
            }
        ],
    }


def _manual_param(name: str, value: str) -> dict[str, Any]:
    return {
        "binding_id": "",
        "param_name": name,
        "param_type": "string",
        "value_mode": "manual",
        "param_value": value,
        "value_source": "default",
    }


def _is_remote_source(node: dict[str, Any]) -> bool:
    skill = node.get("skill") or {}
    skill_id = str(skill.get("skill_id", "") or "")
    skill_name = str(skill.get("skill_name", "") or "")
    return (
        skill_id == REMOTE_SOURCE_BUNDLE
        or skill_name == "remote_source_stop"
        or skill_id == CORPUS_DATASET_SOURCE_BUNDLE
        or skill_name == "corpus_dataset_source_stop"
    )


def _require_remote_node_id(node: dict[str, Any]) -> str:
    for param in node.get("input_params", []) or []:
        if param.get("param_name") == "node_id":
            value = str(param.get("param_value", "") or "").strip()
            if value:
                return value
            break
    raise ValueError(f"remote source node missing node_id param: {node.get('node_id')}")


def _read_remote_node_resource(node: dict[str, Any]) -> RemoteNodeResource:
    skill = node.get("skill") or {}
    skill_id = str(skill.get("skill_id", "") or "")
    skill_name = str(skill.get("skill_name", "") or "")
    if skill_id == CORPUS_DATASET_SOURCE_BUNDLE or skill_name == "corpus_dataset_source_stop":
        return _read_corpus_dataset_source_resource(node)

    params = node.get("input_params", []) or []
    values = {
        str(param.get("param_name", "") or ""): param.get("param_value", "")
        for param in params
    }
    node_id = _require_remote_node_id(node)
    return RemoteNodeResource(
        node_id=node_id,
        cpu_cores=_read_numeric_param(values, "cpu_cores", legacy_keys=("cpu",)),
        memory_gb=_read_numeric_param(values, "memory_gb", legacy_keys=("memory",)),
        free_disk_gb=_read_numeric_param(
            values,
            "free_disk_gb",
            legacy_keys=("disk", "disk_gb", "available_disk_gb"),
        ),
        remote_grpc_target=_read_remote_grpc_target(node),
    )


def _read_corpus_dataset_source_resource(node: dict[str, Any]) -> RemoteNodeResource:
    dataset_id = _read_dataset_id(node)
    from runtime.cross_dag.config import get_cross_dc_config, resolve_cross_dc_config
    from runtime.cross_dag.registry_stub import get_registry

    registry = get_registry()
    dataset = registry.get_dataset(dataset_id)
    if dataset is None:
        raise ValueError(f"dataset_id {dataset_id} is not registered")
    replicas = list(registry.list_replicas(dataset_id))
    if not replicas:
        raise ValueError(f"dataset_id {dataset_id} has no registered replica")

    available = [replica for replica in replicas if str(replica.status).upper() == "AVAILABLE"]
    replica = (available or replicas)[0]
    sources = {source.center_id: source for source in registry.list_sources()}
    source = sources.get(replica.source_ip)
    if source is None:
        raise ValueError(
            f"dataset_id {dataset_id} references unknown source {replica.source_ip}"
        )

    config = resolve_cross_dc_config(get_cross_dc_config(), registry)
    remote_grpc_target = config.endpoint_of(source.center_id)
    connector_id = str(source.source_id or source.center_id).strip()
    resource = {**source.metrics, **replica.metrics}

    return RemoteNodeResource(
        node_id=connector_id,
        cpu_cores=float(resource.get("cpu_cores", 0.0) or 0.0),
        memory_gb=float(resource.get("memory_gb", 0.0) or 0.0),
        free_disk_gb=float(resource.get("free_disk_gb", 0.0) or 0.0),
        remote_grpc_target=remote_grpc_target,
    )


def _read_dataset_id(node: dict[str, Any]) -> str:
    for param in node.get("input_params", []) or []:
        if param.get("param_name") == "dataset_id":
            value = str(param.get("param_value", "") or "").strip()
            if value:
                return value
            break
    raise ValueError(f"corpus dataset source node missing dataset_id param: {node.get('node_id')}")


def _read_remote_grpc_target(node: dict[str, Any]) -> str:
    for param in node.get("input_params", []) or []:
        if param.get("param_name") == "remote_grpc_target":
            value = str(param.get("param_value", "") or "").strip()
            if value:
                return value
            break
    # Backward compatibility for older DAG definitions that only carried
    # node_id and implicitly reused it as the remote submission target.
    return _require_remote_node_id(node)


def _read_numeric_param(
    values: dict[str, Any],
    key: str,
    *,
    legacy_keys: tuple[str, ...] = (),
) -> float:
    for candidate in (key, *legacy_keys):
        if candidate not in values:
            continue
        raw = values.get(candidate)
        if raw in (None, ""):
            return 0.0
        try:
            value = float(str(raw).strip())
        except (TypeError, ValueError) as exc:
            raise ValueError(f"remote source param '{key}' must be numeric") from exc
        if value < 0:
            raise ValueError(f"remote source param '{key}' must be non-negative")
        return value
    return 0.0


def _choose_execution_node_id(
    resources: list[RemoteNodeResource],
    *,
    random_seed: int | None,
) -> str:
    if not resources:
        raise ValueError("no remote node resources available")

    ranked = sorted(
        resources,
        key=lambda item: (
            item.cpu_cores,
            item.memory_gb,
            item.free_disk_gb,
        ),
        reverse=True,
    )
    best = ranked[0]
    tied = [
        item for item in ranked
        if (
            item.cpu_cores == best.cpu_cores
            and item.memory_gb == best.memory_gb
            and item.free_disk_gb == best.free_disk_gb
        )
    ]
    return random.Random(random_seed).choice(tied).node_id
