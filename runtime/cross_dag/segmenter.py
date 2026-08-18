"""分层分段：把绑定好中心的 DAG 切成若干执行单元，并保证单元图无环。"""

from __future__ import annotations

from .schema import CrossDagError, LogicalDag, Segment, SegmentGraph


def build_segment_graph(dag: LogicalDag, center_of: dict[str, str]) -> SegmentGraph:
    missing = [node.node_id for node in dag.nodes if node.node_id not in center_of]
    if missing:
        raise CrossDagError(f"以下节点未完成位置绑定: {missing}")

    levels = compute_levels(dag, center_of)
    segment_of = merge_same_center_segments(
        dag,
        center_of,
        levels,
        {node_id: _segment_id(center_of[node_id], levels[node_id]) for node_id in levels},
    )

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
        segment.level = min(segment.level, levels[node_id])
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


def merge_same_center_segments(
    dag: LogicalDag,
    center_of: dict[str, str],
    levels: dict[str, int],
    segment_of: dict[str, str],
) -> dict[str, str]:
    """把同一中心的段尽量合回一个执行单元。

    分层是为了让单元图无环 —— 不能按中心朴素分组，A->B->A 会成环。代价是同一
    中心的节点会因层级不同被切开：一个节点只要有任意一条上游是跨中心的，它的层级
    就被抬高，于是同中心的上游落到了另一段。这些边随后会被当成跨域边，白白套上一次
    「导出文件 + gRPC 子 DAG」，而两端本来就在同一台机器上。

    这里在「合并后仍然无环」的前提下把同中心的段合回去。这是纯优化，不改变节点的
    执行位置，也不改变数据流；合并会成环的情况（本地边与绕远端的路径并存）保持拆开，
    由 nester 以就地内联的方式兜底，同样不会产生指向本机的远程调用。
    """
    roots = {segment_id: segment_id for segment_id in set(segment_of.values())}
    center_of_segment = {
        segment_id: center_of[node_id] for node_id, segment_id in segment_of.items()
    }

    def find(segment_id: str) -> str:
        root = segment_id
        while roots[root] != root:
            root = roots[root]
        while roots[segment_id] != root:
            roots[segment_id], segment_id = root, roots[segment_id]
        return root

    def quotient(pending: tuple[str, str] | None) -> tuple[set[str], set[tuple[str, str]]]:
        """把段折叠成执行单元后的商图。pending 表示「再试着合并这一对」。"""
        mapping = {segment_id: find(segment_id) for segment_id in roots}
        if pending is not None:
            keep, drop = pending
            mapping = {
                segment_id: (keep if root == drop else root)
                for segment_id, root in mapping.items()
            }
        edges = {
            (mapping[segment_of[b.from_node_id]], mapping[segment_of[b.to_node_id]])
            for b in dag.bindings
            if mapping[segment_of[b.from_node_id]] != mapping[segment_of[b.to_node_id]]
        }
        return set(mapping.values()), edges

    while True:
        merged_any = False
        by_center: dict[str, list[str]] = {}
        for segment_id in sorted(roots):
            root = find(segment_id)
            bucket = by_center.setdefault(center_of_segment[root], [])
            if root not in bucket:
                bucket.append(root)

        for center_id in sorted(by_center):
            candidates = by_center[center_id]
            for index, left in enumerate(candidates):
                for right in candidates[index + 1 :]:
                    keep, drop = find(left), find(right)
                    if keep == drop:
                        continue
                    if _is_acyclic(*quotient((keep, drop))):
                        roots[drop] = keep
                        merged_any = True
        if not merged_any:
            break

    # 单元命名沿用 中心#层级，取组内最小层级。同一中心的每个层级只属于一个组，
    # 所以同中心的不同单元不会重名。
    group_level: dict[str, int] = {}
    for node_id, segment_id in segment_of.items():
        root = find(segment_id)
        level = levels[node_id]
        if root not in group_level or level < group_level[root]:
            group_level[root] = level

    canonical = {
        root: _segment_id(center_of_segment[root], level)
        for root, level in group_level.items()
    }
    return {
        node_id: canonical[find(segment_id)] for node_id, segment_id in segment_of.items()
    }


def assert_segment_graph_acyclic(graph: SegmentGraph) -> None:
    """单元图无环由分层算法保证，合并只在保持无环时进行；这里断言一次防止回归。"""
    edges = {
        (graph.segment_of[b.from_node_id], graph.segment_of[b.to_node_id])
        for b in graph.cross_edges
    }
    if _is_acyclic(set(graph.segments), edges):
        return

    indegree = {seg_id: 0 for seg_id in graph.segments}
    for _, target in edges:
        indegree[target] += 1
    cyclic = [seg_id for seg_id, degree in indegree.items() if degree > 0]
    raise CrossDagError(f"段图存在环，无法嵌套构造。涉及段: {sorted(cyclic)}")


def _is_acyclic(nodes: set[str], edges: set[tuple[str, str]]) -> bool:
    indegree = {node: 0 for node in nodes}
    adjacency: dict[str, list[str]] = {node: [] for node in nodes}
    for source, target in edges:
        adjacency[source].append(target)
        indegree[target] += 1

    queue = [node for node, degree in indegree.items() if degree == 0]
    visited = 0
    while queue:
        current = queue.pop()
        visited += 1
        for nxt in adjacency[current]:
            indegree[nxt] -= 1
            if indegree[nxt] == 0:
                queue.append(nxt)
    return visited == len(nodes)


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
