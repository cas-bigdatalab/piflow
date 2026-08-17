"""分层分段：把绑定好中心的 DAG 切成若干段，并保证段图无环。"""

from __future__ import annotations

from .schema import CrossDagError, LogicalDag, Segment, SegmentGraph


def build_segment_graph(dag: LogicalDag, center_of: dict[str, str]) -> SegmentGraph:
    missing = [node.node_id for node in dag.nodes if node.node_id not in center_of]
    if missing:
        raise CrossDagError(f"以下节点未完成位置绑定: {missing}")

    levels = compute_levels(dag, center_of)
    segment_of = {
        node_id: _segment_id(center_of[node_id], levels[node_id]) for node_id in levels
    }

    segments: dict[str, Segment] = {}
    for node_id, segment_id in segment_of.items():
        segment = segments.get(segment_id)
        if segment is None:
            segment = Segment(
                segment_id=segment_id,
                center_id=center_of[node_id],
                level=levels[node_id],
                node_ids=[],
            )
            segments[segment_id] = segment
        segment.node_ids.append(node_id)

    for segment in segments.values():
        segment.node_ids.sort()

    cross_edges = [
        binding
        for binding in dag.bindings
        if segment_of[binding.from_node_id] != segment_of[binding.to_node_id]
    ]

    graph = SegmentGraph(
        segments=segments,
        segment_of=segment_of,
        levels=levels,
        cross_edges=cross_edges,
    )
    assert_segment_graph_acyclic(graph)
    return graph


def compute_levels(dag: LogicalDag, center_of: dict[str, str]) -> dict[str, int]:
    levels: dict[str, int] = {}
    for node_id in _topological_order(dag):
        predecessors = dag.predecessors(node_id)
        if not predecessors:
            levels[node_id] = 0
            continue
        levels[node_id] = max(
            levels[pred] + (0 if center_of[pred] == center_of[node_id] else 1)
            for pred in predecessors
        )
    return levels


def assert_segment_graph_acyclic(graph: SegmentGraph) -> None:
    """段图无环由分层算法保证，这里断言一次，防止改动引入回归。"""
    adjacency: dict[str, set[str]] = {seg_id: set() for seg_id in graph.segments}
    indegree = {seg_id: 0 for seg_id in graph.segments}

    for binding in graph.cross_edges:
        upstream = graph.segment_of[binding.from_node_id]
        downstream = graph.segment_of[binding.to_node_id]
        if downstream in adjacency[upstream]:
            continue
        adjacency[upstream].add(downstream)
        indegree[downstream] += 1

    queue = [seg_id for seg_id, degree in indegree.items() if degree == 0]
    visited = 0
    while queue:
        current = queue.pop()
        visited += 1
        for nxt in adjacency[current]:
            indegree[nxt] -= 1
            if indegree[nxt] == 0:
                queue.append(nxt)

    if visited != len(graph.segments):
        cyclic = [seg_id for seg_id, degree in indegree.items() if degree > 0]
        raise CrossDagError(f"段图存在环，无法嵌套构造。涉及段: {sorted(cyclic)}")


def _segment_id(center_id: str, level: int) -> str:
    return f"{center_id}#{level}"


def _topological_order(dag: LogicalDag) -> list[str]:
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
        raise CrossDagError("逻辑 DAG 中存在环")
    return order
