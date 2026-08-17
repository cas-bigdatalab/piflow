"""位置绑定：确定每个节点在哪个中心执行。"""

from __future__ import annotations

from collections import Counter

from .schema import (
    DATASET_URI_PREFIX,
    BindResult,
    CrossDagError,
    IntentDataset,
    IntentSpec,
    LogicalDag,
    LogicalNode,
    ReplicaDecision,
)
from .selector import select_replica

_LOCATOR_PARAM_NAMES = ("file_path", "input_file_path", "path", "input", "locator")


def bind_centers(
    dag: LogicalDag,
    intent: IntentSpec,
    *,
    default_center_id: str,
    known_centers: set[str] | None = None,
    replica_weights: dict[str, float] | None = None,
    available_statuses: frozenset[str] | set[str] | None = None,
    metric_directions: dict[str, str] | None = None,
) -> BindResult:
    result = BindResult()
    node_map = dag.node_map()
    source_ids = set(dag.source_node_ids())

    for node_id in _topological_order(dag):
        node = node_map[node_id]

        explicit = (node.data_center or "").strip()

        if node_id in source_ids:
            dataset = _match_dataset(node, intent)
            if dataset is not None and dataset.replicas:
                preferred = explicit or _preferred_center(
                    dag, node_id, node_map, default_center_id
                )
                decision = select_replica(
                    dataset,
                    preferred_center_id=preferred,
                    node_id=node_id,
                    weights=replica_weights,
                    directions=metric_directions,
                    known_centers=known_centers,
                    available_statuses=available_statuses,
                    required_center_id=explicit,
                )
                result.replica_decisions.append(decision)
                _apply_replica(node, decision)
                result.center_of[node_id] = decision.chosen.center_id
                prefix = "显式标注 dataCenter，" if explicit else ""
                result.reasons[node_id] = (
                    f"{prefix}数据源节点，副本挑选 -> {decision.chosen.replica_id}"
                    f"（{decision.reason}）"
                )
                continue

            if explicit:
                result.center_of[node_id] = explicit
                result.reasons[node_id] = "显式标注 dataCenter"
                continue

            if dataset is not None and dataset.center_id:
                result.center_of[node_id] = dataset.center_id
                result.reasons[node_id] = f"数据源节点，跟随数据集 {dataset.alias} 所在中心"
                continue

            result.center_of[node_id] = default_center_id
            result.reasons[node_id] = "数据源节点未匹配到已注册数据集，使用默认中心"
            continue

        if explicit:
            result.center_of[node_id] = explicit
            result.reasons[node_id] = "显式标注 dataCenter"
            continue

        inherited = _inherit_from_upstream(dag, node_id, result.center_of)
        if inherited is not None:
            result.center_of[node_id] = inherited
            result.reasons[node_id] = "继承上游中心（数据就近）"
            continue

        result.center_of[node_id] = default_center_id
        result.reasons[node_id] = "无上游可继承，使用默认中心"

    if known_centers:
        unknown = {
            center for center in result.center_of.values() if center not in known_centers
        }
        if unknown:
            raise CrossDagError(
                f"绑定到了未在 config/cross_dc.yaml 中注册的中心: {sorted(unknown)}"
            )

    for node in dag.nodes:
        node.data_center = result.center_of[node.node_id]

    return result


def _match_dataset(node: LogicalNode, intent: IntentSpec) -> IntentDataset | None:
    """把数据源节点对应到意图里的某个逻辑数据集。"""
    values = _locator_values(node)

    for value in values:
        if value.startswith(DATASET_URI_PREFIX):
            dataset_id = value[len(DATASET_URI_PREFIX) :].strip().strip("/")
            for dataset in intent.datasets:
                if dataset.dataset_id == dataset_id or dataset.alias == dataset_id:
                    return dataset
            raise CrossDagError(
                f"节点 {node.node_id} 引用了意图中不存在的数据集: {dataset_id}"
            )

    for dataset in intent.datasets:
        known = [r.locator for r in dataset.replicas] + [dataset.locator]
        for value in values:
            if any(candidate and _same_locator(value, candidate) for candidate in known):
                return dataset

    haystack = node.node_name or ""
    for dataset in intent.datasets:
        if dataset.alias and dataset.alias in haystack:
            return dataset
        if dataset.name and dataset.name in haystack:
            return dataset

    return None


def _locator_values(node: LogicalNode) -> list[str]:
    values: list[str] = []
    for name in _LOCATOR_PARAM_NAMES:
        param = node.input_param(name)
        if param is None or param.value_mode != "manual":
            continue
        text = str(param.param_value).strip()
        if text:
            values.append(text)
    return values


def _apply_replica(node: LogicalNode, decision: ReplicaDecision) -> None:
    """把选中副本的真实访问路径回写到节点参数上。"""
    if decision.chosen is None:
        return
    for name in _LOCATOR_PARAM_NAMES:
        param = node.input_param(name)
        if param is None or param.value_mode != "manual":
            continue
        param.param_value = decision.chosen.locator
        return


def _preferred_center(
    dag: LogicalDag,
    node_id: str,
    node_map: dict[str, LogicalNode],
    default_center_id: str,
) -> str:
    """数据源节点的偏好中心 = 直接下游里已显式钉死的中心。"""
    downstream = [
        (node_map[succ].data_center or "").strip()
        for succ in dag.successors(node_id)
        if succ in node_map
    ]
    pinned = [center for center in downstream if center]
    if not pinned:
        return default_center_id
    counter = Counter(pinned)
    top = max(counter.values())
    return sorted(center for center, count in counter.items() if count == top)[0]


def _same_locator(left: str, right: str) -> bool:
    return left.strip().lstrip("/").lower() == right.strip().lstrip("/").lower()


def _inherit_from_upstream(
    dag: LogicalDag,
    node_id: str,
    center_of: dict[str, str],
) -> str | None:
    upstream_centers = [
        center_of[pred] for pred in dag.predecessors(node_id) if pred in center_of
    ]
    if not upstream_centers:
        return None
    counter = Counter(upstream_centers)
    top = max(counter.values())
    return sorted(center for center, count in counter.items() if count == top)[0]


def _topological_order(dag: LogicalDag) -> list[str]:
    """Kahn 拓扑排序，保证绑定处理节点时上游已定。"""
    node_ids = [node.node_id for node in dag.nodes]
    indegree = {node_id: 0 for node_id in node_ids}
    adjacency: dict[str, list[str]] = {node_id: [] for node_id in node_ids}

    for binding in dag.bindings:
        if binding.from_node_id not in indegree or binding.to_node_id not in indegree:
            raise CrossDagError(
                f"binding 引用了不存在的节点: {binding.from_node_id} -> {binding.to_node_id}"
            )
        adjacency[binding.from_node_id].append(binding.to_node_id)
        indegree[binding.to_node_id] += 1

    queue = sorted(node_id for node_id, degree in indegree.items() if degree == 0)
    order: list[str] = []
    while queue:
        current = queue.pop(0)
        order.append(current)
        for nxt in adjacency[current]:
            indegree[nxt] -= 1
            if indegree[nxt] == 0:
                queue.append(nxt)
        queue.sort()

    if len(order) != len(node_ids):
        raise CrossDagError("逻辑 DAG 中存在环，无法完成位置绑定")
    return order
