"""递归嵌套构造 —— 本模块是整套方案的核心。"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from .schema import (
    BUNDLE_REMOTE_SUBDAG,
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
    logical_node_to_execution_dsl,
)


@dataclass
class NestContext:
    dag: LogicalDag
    graph: SegmentGraph
    endpoint_of: dict[str, str]
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
    # Kept in the public signature for config/backward compatibility. Remote
    # results are now selected directly by producer node/output, so no
    # synthetic FileSaveStop or export directory is needed.
    _ = export_dir
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
    """构造某个执行单元所在层的 DSL。

    只有真正跨中心的上游才导出成文件、包成远程子 DAG；同中心的上游单元就地内联到本层
    —— 两端在同一台机器上，没有任何需要传输的东西，套一次远程调用只会凭空多出一次
    文件导出、一次 gRPC 自调用和一次下载。
    """
    center_id = ctx.graph.segments[segment_id].center_id
    nodes: dict[str, dict[str, Any]] = {}
    bindings: dict[str, dict[str, str]] = {}
    absorbed: set[str] = set()
    remote_of: dict[tuple[str, str], str] = {}

    def absorb(unit_id: str, chain: tuple[str, ...]) -> None:
        if unit_id in absorbed:
            return
        if unit_id in chain:
            raise CrossDagError(f"嵌套构造检测到环: {' -> '.join((*chain, unit_id))}")
        absorbed.add(unit_id)
        ctx.nest_count[unit_id] = ctx.nest_count.get(unit_id, 0) + 1

        segment = ctx.graph.segments[unit_id]
        member_ids = set(segment.node_ids)
        for node_id in segment.node_ids:
            nodes[node_id] = logical_node_to_execution_dsl(ctx.node_map[node_id])
        for binding in ctx.dag.bindings:
            if binding.from_node_id in member_ids and binding.to_node_id in member_ids:
                bindings[binding.binding_id] = binding.to_dsl()

        incoming: dict[tuple[str, str], list[Binding]] = {}
        for binding in ctx.graph.cross_edges:
            if ctx.graph.segment_of[binding.to_node_id] != unit_id:
                continue
            incoming.setdefault(
                (binding.from_node_id, binding.from_param_name), []
            ).append(binding)

        for (producer_id, producer_param), edges in sorted(incoming.items()):
            upstream_id = ctx.graph.segment_of[producer_id]
            upstream = ctx.graph.segments[upstream_id]

            if upstream.center_id == center_id:
                # 同一台机器：把上游单元并进本层，原绑定直接可用。
                absorb(upstream_id, (*chain, unit_id))
                for edge in edges:
                    bindings[edge.binding_id] = edge.to_dsl()
                continue

            remote_node_id = remote_of.get((producer_id, producer_param))
            if remote_node_id is None:
                remote_node_id = _attach_remote_branch(
                    ctx,
                    nodes=nodes,
                    producer_id=producer_id,
                    producer_param=producer_param,
                    upstream_id=upstream_id,
                    upstream_center_id=upstream.center_id,
                    chain=(*chain, unit_id),
                )
                remote_of[(producer_id, producer_param)] = remote_node_id

            for edge in edges:
                binding = Binding(
                    from_node_id=remote_node_id,
                    from_param_name=REMOTE_OUTPUT_PORT,
                    to_node_id=edge.to_node_id,
                    to_param_name=edge.to_param_name,
                )
                bindings[binding.binding_id] = binding.to_dsl()

    absorb(segment_id, path)

    return build_dsl(
        task_id=f"{ctx.task_id}--{segment_id}" if path else ctx.task_id,
        task_name=f"{ctx.task_name} [{segment_id}]" if path else ctx.task_name,
        nodes=list(nodes.values()),
        bindings=list(bindings.values()),
    )


def _attach_remote_branch(
    ctx: NestContext,
    *,
    nodes: dict[str, dict[str, Any]],
    producer_id: str,
    producer_param: str,
    upstream_id: str,
    upstream_center_id: str,
    chain: tuple[str, ...],
) -> str:
    """把一条真正跨中心的上游分支包成远程子 DAG，挂到当前层，返回远程节点 id。"""
    child_dsl = _build_segment_dsl(upstream_id, ctx, path=chain)

    remote_node = _make_remote_node(
        producer_id=producer_id,
        producer_param=producer_param,
        upstream_center_id=upstream_center_id,
        endpoint=_require_endpoint(ctx, upstream_center_id),
        child_dsl=child_dsl,
        result_node_id=producer_id,
        result_output_name=producer_param,
        wait_timeout_seconds=ctx.wait_timeout_seconds,
    )
    nodes[remote_node.node_id] = logical_node_to_execution_dsl(remote_node)
    return remote_node.node_id


def _make_remote_node(
    *,
    producer_id: str,
    producer_param: str,
    upstream_center_id: str,
    endpoint: str,
    child_dsl: dict[str, Any],
    result_node_id: str,
    result_output_name: str,
    wait_timeout_seconds: int,
) -> LogicalNode:
    output_suffix = "" if producer_param == REMOTE_OUTPUT_PORT else f"-{producer_param}"
    node_id = f"{REMOTE_NODE_PREFIX}{producer_id}{output_suffix}"

    return LogicalNode(
        node_id=node_id,
        node_name=f"跨域执行_{upstream_center_id}",
        skill_id=BUNDLE_REMOTE_SUBDAG,
        skill_name="remoteSubDagSourceNode",
        node_type="synthetic_remote_source",
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
                param_name="result_output_name",
                value_mode="manual",
                param_value=result_output_name,
                param_type="string",
            ),
            InputParam(
                param_name="wait_timeout_seconds",
                value_mode="manual",
                param_value=str(wait_timeout_seconds),
                param_type="string",
            ),
        ],
        out_params=[OutParam(param_name=REMOTE_OUTPUT_PORT, param_type="file_artifact")],
    )


def _require_endpoint(ctx: NestContext, center_id: str) -> str:
    endpoint = ctx.endpoint_of.get(center_id, "")
    if not endpoint:
        raise CrossDagError(
            f"中心 {center_id} 未配置 grpc_endpoint，请检查 config/cross_dc.yaml"
        )
    return endpoint
