"""递归嵌套构造 —— 本模块是整套方案的核心。"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from .schema import (
    BUNDLE_FILE_SAVE,
    BUNDLE_REMOTE_SUBDAG,
    EXPORT_NODE_PREFIX,
    FILE_SAVE_INPUT_PORT,
    REMOTE_NODE_PREFIX,
    REMOTE_OUTPUT_PORT,
    Binding,
    CrossDagError,
    InputParam,
    LogicalDag,
    LogicalNode,
    OutParam,
    SegmentGraph,
    build_dsl,
)


@dataclass
class NestContext:
    dag: LogicalDag
    graph: SegmentGraph
    endpoint_of: dict[str, str]
    export_dir: str
    wait_timeout_seconds: int
    task_id: str
    task_name: str
    node_map: dict[str, LogicalNode] = field(default_factory=dict)
    nest_count: dict[str, int] = field(default_factory=dict)


def build_nested_dsl(
    dag: LogicalDag,
    graph: SegmentGraph,
    *,
    endpoint_of: dict[str, str],
    export_dir: str,
    task_id: str,
    task_name: str,
    wait_timeout_seconds: int = 3600,
) -> tuple[dict[str, Any], dict[str, int]]:
    """返回 (最外层 DSL, 每个段被嵌套的次数)。"""
    roots = graph.root_segments()
    if not roots:
        raise CrossDagError("段图没有终点段，无法确定最外层")
    if len(roots) > 1:
        raise CrossDagError(
            f"检测到 {len(roots)} 个终点段 {roots}；"
            "嵌套模型要求单一终点，请让所有分支汇聚到同一个输出节点后再规划"
        )

    ctx = NestContext(
        dag=dag,
        graph=graph,
        endpoint_of=endpoint_of,
        export_dir=export_dir.rstrip("/") or "/artifacts/xdc",
        wait_timeout_seconds=wait_timeout_seconds,
        task_id=task_id,
        task_name=task_name,
        node_map=dag.node_map(),
    )

    dsl = _build_segment_dsl(roots[0], ctx, path=())
    return dsl, dict(ctx.nest_count)


def _build_segment_dsl(
    segment_id: str,
    ctx: NestContext,
    *,
    path: tuple[str, ...],
) -> dict[str, Any]:
    if segment_id in path:
        raise CrossDagError(f"嵌套构造检测到环: {' -> '.join((*path, segment_id))}")

    ctx.nest_count[segment_id] = ctx.nest_count.get(segment_id, 0) + 1
    segment = ctx.graph.segments[segment_id]
    member_ids = set(segment.node_ids)

    nodes: list[dict[str, Any]] = [
        ctx.node_map[node_id].to_dsl() for node_id in segment.node_ids
    ]
    bindings: list[dict[str, str]] = [
        binding.to_dsl()
        for binding in ctx.dag.bindings
        if binding.from_node_id in member_ids and binding.to_node_id in member_ids
    ]

    incoming: dict[tuple[str, str], list[Binding]] = {}
    for binding in ctx.graph.cross_edges:
        if ctx.graph.segment_of[binding.to_node_id] != segment_id:
            continue
        incoming.setdefault((binding.from_node_id, binding.from_param_name), []).append(
            binding
        )

    for (producer_id, producer_param), edges in sorted(incoming.items()):
        upstream_segment_id = ctx.graph.segment_of[producer_id]
        upstream_segment = ctx.graph.segments[upstream_segment_id]

        child_dsl = _build_segment_dsl(
            upstream_segment_id, ctx, path=(*path, segment_id)
        )

        export_node = _make_export_node(
            producer_id=producer_id,
            producer_param=producer_param,
            segment_id=upstream_segment_id,
            export_dir=ctx.export_dir,
            task_id=ctx.task_id,
        )
        export_binding = Binding(
            from_node_id=producer_id,
            from_param_name=producer_param,
            to_node_id=export_node.node_id,
            to_param_name=FILE_SAVE_INPUT_PORT,
        )
        child_dsl = build_dsl(
            task_id=child_dsl["task"]["dag_task_id"],
            task_name=child_dsl["task"]["dag_task_name"],
            nodes=[*child_dsl["nodes"], export_node.to_dsl()],
            bindings=[*child_dsl["bindings"], export_binding.to_dsl()],
        )

        remote_node = _make_remote_node(
            producer_id=producer_id,
            producer_param=producer_param,
            upstream_center_id=upstream_segment.center_id,
            endpoint=_require_endpoint(ctx, upstream_segment.center_id),
            child_dsl=child_dsl,
            result_node_id=export_node.node_id,
            wait_timeout_seconds=ctx.wait_timeout_seconds,
        )
        nodes.append(remote_node.to_dsl())

        for edge in edges:
            bindings.append(
                Binding(
                    from_node_id=remote_node.node_id,
                    from_param_name=REMOTE_OUTPUT_PORT,
                    to_node_id=edge.to_node_id,
                    to_param_name=edge.to_param_name,
                ).to_dsl()
            )

    return build_dsl(
        task_id=f"{ctx.task_id}--{segment_id}" if path else ctx.task_id,
        task_name=f"{ctx.task_name} [{segment_id}]" if path else ctx.task_name,
        nodes=nodes,
        bindings=bindings,
    )


def _make_export_node(
    *,
    producer_id: str,
    producer_param: str,
    segment_id: str,
    export_dir: str,
    task_id: str,
) -> LogicalNode:
    """跨域出口必须挂一个 FileSaveStop。"""
    node_id = f"{EXPORT_NODE_PREFIX}{producer_id}__{producer_param}"
    safe_segment = segment_id.replace("#", "_")
    destination = f"{export_dir}/{task_id}/{safe_segment}/{producer_id}__{producer_param}.dat"

    return LogicalNode(
        node_id=node_id,
        node_name=f"跨域导出_{producer_id}_{producer_param}",
        skill_id=BUNDLE_FILE_SAVE,
        node_type="system",
        data_center="",
        input_params=[
            InputParam(
                param_name=FILE_SAVE_INPUT_PORT,
                value_mode="reference",
                param_value="",
                param_type="file",
                binding_id=f"{producer_id}:{producer_param}->{node_id}:{FILE_SAVE_INPUT_PORT}",
            ),
            InputParam(
                param_name="absolute_path",
                value_mode="manual",
                param_value=destination,
                param_type="string",
            ),
            InputParam(
                param_name="overwrite",
                value_mode="manual",
                param_value="true",
                param_type="string",
            ),
        ],
        out_params=[],
    )


def _make_remote_node(
    *,
    producer_id: str,
    producer_param: str,
    upstream_center_id: str,
    endpoint: str,
    child_dsl: dict[str, Any],
    result_node_id: str,
    wait_timeout_seconds: int,
) -> LogicalNode:
    node_id = f"{REMOTE_NODE_PREFIX}{upstream_center_id}__{producer_id}__{producer_param}"

    return LogicalNode(
        node_id=node_id,
        node_name=f"跨域执行_{upstream_center_id}",
        skill_id=BUNDLE_REMOTE_SUBDAG,
        node_type="system",
        data_center=upstream_center_id,
        input_params=[
            InputParam(
                param_name="remote_grpc_target",
                value_mode="manual",
                param_value=endpoint,
                param_type="string",
            ),
            InputParam(
                param_name="subdag_definition_json",
                value_mode="manual",
                param_value=json.dumps(child_dsl, ensure_ascii=False),
                param_type="string",
            ),
            InputParam(
                param_name="result_node_id",
                value_mode="manual",
                param_value=result_node_id,
                param_type="string",
            ),
            InputParam(
                param_name="wait_timeout_seconds",
                value_mode="manual",
                param_value=str(wait_timeout_seconds),
                param_type="string",
            ),
        ],
        out_params=[OutParam(param_name=REMOTE_OUTPUT_PORT, param_type="file")],
    )


def _require_endpoint(ctx: NestContext, center_id: str) -> str:
    endpoint = ctx.endpoint_of.get(center_id, "")
    if not endpoint:
        raise CrossDagError(
            f"中心 {center_id} 未配置 grpc_endpoint，请检查 config/cross_dc.yaml"
        )
    return endpoint
