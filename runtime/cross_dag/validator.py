"""编译期校验：宁可在提交前报错，也不要让坏 DAG 跑到一半失败。"""

from __future__ import annotations

import json
from typing import Any

from .schema import (
    BUNDLE_FILE_SAVE,
    DATASET_URI_PREFIX,
    EXPORT_NODE_PREFIX,
    REMOTE_NODE_PREFIX,
    LogicalDag,
    SegmentGraph,
    ValidationReport,
)

SINK_BUNDLES = {
    BUNDLE_FILE_SAVE,
    "piflow_engine.cn.piflow.engine.local.dataspace_file_sink_stop.DataspaceFileSinkStop",
    "piflow_engine.cn.piflow.engine.local.llm_file_transform_stop.LlmFileTransformStop",
}


def validate_logical_dag(dag: LogicalDag) -> ValidationReport:
    report = ValidationReport()
    node_ids = {node.node_id for node in dag.nodes}

    if not dag.nodes:
        report.error("逻辑 DAG 为空，没有任何节点")
        return report

    duplicates = _duplicates([node.node_id for node in dag.nodes])
    if duplicates:
        report.error(f"存在重复的 node_id: {sorted(duplicates)}")

    for node in dag.nodes:
        if not node.skill_id:
            report.error(f"节点 {node.node_id} 缺少 skill_id")

    for binding in dag.bindings:
        if binding.from_node_id not in node_ids:
            report.error(f"binding 引用了不存在的上游节点: {binding.from_node_id}")
        if binding.to_node_id not in node_ids:
            report.error(f"binding 引用了不存在的下游节点: {binding.to_node_id}")
        if not binding.from_param_name:
            report.error(f"binding {binding.binding_id} 缺少 from_param_name")
        if not binding.to_param_name:
            report.error(f"binding {binding.binding_id} 缺少 to_param_name")

    sinks = dag.sink_node_ids()
    if not sinks:
        report.error("逻辑 DAG 没有终点节点，可能存在环")
    elif len(sinks) > 1:
        report.warn(
            f"存在多个终点节点 {sorted(sinks)}；嵌套模型要求单一终点，"
            "跨域规划会失败。请在规划阶段汇聚到一个输出节点"
        )

    return report


def validate_location_hints(
    intent: Any,
    center_of: dict[str, str],
    location_term: str = "执行位置",
) -> ValidationReport:
    """用户明确要求的执行位置，必须真的出现在绑定结果里。"""
    report = ValidationReport()
    hints = getattr(intent, "location_hints", None) or []
    if not hints:
        return report

    used = set(center_of.values())
    for hint in hints:
        center_id = getattr(hint, "center_id", "")
        if center_id and center_id not in used:
            raw = getattr(hint, "raw", "") or getattr(hint, "applies_to", "")
            report.error(
                f"用户要求在 {center_id} 执行（原话：{raw or '未记录'}），"
                f"但规划结果没有任何节点绑定到它，实际只用到 {sorted(used)}。"
                f"跨{location_term}要求被忽略了，请检查规划是否退化成单一{location_term}"
            )
    return report


def validate_intent_coverage(intent: Any, dag: LogicalDag) -> ValidationReport:
    """意图层认下的数据集，必须真的出现在 DAG 里。"""
    report = ValidationReport()
    datasets = getattr(intent, "datasets", None) or []
    if not datasets:
        return report

    referenced = set()
    for node in dag.nodes:
        for param in node.input_params:
            value = str(param.param_value or "")
            if value.startswith(DATASET_URI_PREFIX):
                referenced.add(value[len(DATASET_URI_PREFIX):].strip().strip("/"))
            elif value:
                referenced.add(value)

    for dataset in datasets:
        dataset_id = getattr(dataset, "dataset_id", "") or ""
        alias = getattr(dataset, "alias", "") or ""
        if dataset_id in referenced or alias in referenced:
            continue
        locators = {getattr(dataset, "locator", "") or ""} | {
            getattr(r, "locator", "") or "" for r in getattr(dataset, "replicas", None) or []
        }
        if locators & referenced:
            continue
        report.warn(
            f"意图识别选中了数据集 {dataset_id or alias}"
            f"（{getattr(dataset, 'name', '') or '未命名'}），但规划出的 DAG 没有任何节点读取它。"
            "请确认它是被规划器判断为不需要，还是因为算子表达不了而绕过去了 —— "
            "后者意味着相关参数可能是模型编的字面量，不是从该数据集读来的"
        )
    return report


def validate_segmentation(
    dag: LogicalDag,
    graph: SegmentGraph,
    nest_count: dict[str, int],
) -> ValidationReport:
    report = ValidationReport()

    roots = graph.root_segments()
    if len(roots) != 1:
        report.error(f"段图必须有且仅有一个终点段，实际为 {roots}")

    for segment_id, count in sorted(nest_count.items()):
        if count > 1:
            segment = graph.segments[segment_id]
            report.warn(
                f"段 {segment_id}（中心 {segment.center_id}，含 {len(segment.node_ids)} 个节点）"
                f"被嵌套了 {count} 次，将被重复执行 {count} 遍。"
                "这是菱形跨域依赖导致的，属于嵌套模型的固有限制；"
                "若代价不可接受，请把相关分支合并到同一中心"
            )

    exports_per_segment: dict[str, set[str]] = {}
    for binding in graph.cross_edges:
        upstream = graph.segment_of[binding.from_node_id]
        exports_per_segment.setdefault(upstream, set()).add(
            f"{binding.from_node_id}:{binding.from_param_name}"
        )
    for segment_id, ports in sorted(exports_per_segment.items()):
        if len(ports) > 1:
            report.warn(
                f"段 {segment_id} 有 {len(ports)} 个跨域出口 {sorted(ports)}，"
                "每个出口会各自嵌套一份该段，导致重复执行"
            )

    return report


def validate_nested_dsl(dsl: dict[str, Any], *, depth: int = 0) -> ValidationReport:
    """递归校验嵌套 DSL 的结构完整性。"""
    report = ValidationReport()
    prefix = f"[第{depth}层] "

    for key in ("dsl_version", "task", "nodes", "edges", "bindings"):
        if key not in dsl:
            report.error(f"{prefix}DSL 缺少字段 {key}")
    if report.errors:
        return report

    nodes = dsl["nodes"]
    bindings = dsl["bindings"]
    node_ids = {str(node.get("node_id", "")) for node in nodes}

    if not nodes:
        report.error(f"{prefix}DSL 没有任何节点")
        return report

    for node in nodes:
        node_id = str(node.get("node_id", ""))
        skill_id = str((node.get("skill") or {}).get("skill_id", ""))
        if not node_id:
            report.error(f"{prefix}存在缺少 node_id 的节点")
        if not skill_id:
            report.error(f"{prefix}节点 {node_id} 缺少 skill.skill_id")

    for binding in bindings:
        for side in ("from_node_id", "to_node_id"):
            ref = str(binding.get(side, ""))
            if ref not in node_ids:
                report.error(f"{prefix}binding 的 {side}={ref} 在本层节点中不存在")
        if not binding.get("from_param_name"):
            report.error(f"{prefix}binding 缺少 from_param_name")
        if not binding.get("to_param_name"):
            report.error(f"{prefix}binding 缺少 to_param_name")

    edge_pairs = {
        (str(e.get("from_node_id")), str(e.get("to_node_id"))) for e in dsl["edges"]
    }
    binding_pairs = {
        (str(b.get("from_node_id")), str(b.get("to_node_id"))) for b in bindings
    }
    if edge_pairs != binding_pairs:
        report.error(
            f"{prefix}edges 与 bindings 的节点对不一致，"
            f"仅在 edges: {sorted(edge_pairs - binding_pairs)}，"
            f"仅在 bindings: {sorted(binding_pairs - edge_pairs)}"
        )

    for node in nodes:
        node_id = str(node.get("node_id", ""))
        if not node_id.startswith(REMOTE_NODE_PREFIX):
            continue

        params = {
            str(p.get("param_name")): p.get("param_value")
            for p in node.get("input_params") or []
        }

        if not str(params.get("remote_grpc_target", "")).strip():
            report.error(f"{prefix}远程节点 {node_id} 缺少 remote_grpc_target")

        raw_child = params.get("subdag_definition_json", "")
        if not raw_child:
            report.error(f"{prefix}远程节点 {node_id} 缺少 subdag_definition_json")
            continue

        try:
            child = json.loads(raw_child)
        except json.JSONDecodeError as exc:
            report.error(f"{prefix}远程节点 {node_id} 的 subdag_definition_json 不是合法 JSON: {exc}")
            continue

        child_report = validate_nested_dsl(child, depth=depth + 1)
        report.merge(child_report)

        result_node_id = str(params.get("result_node_id", "") or "")
        child_node_ids = {str(n.get("node_id", "")) for n in child.get("nodes") or []}
        if result_node_id:
            if result_node_id not in child_node_ids:
                report.error(
                    f"{prefix}远程节点 {node_id} 的 result_node_id={result_node_id} "
                    "在子 DAG 中不存在"
                )
        else:
            report.warn(
                f"{prefix}远程节点 {node_id} 未指定 result_node_id，"
                "远端将取最后一个写了 final_output_path 的 stop，多出口时结果不确定"
            )

        child_report_sink = _check_child_has_export(child, prefix=f"[第{depth + 1}层] ")
        report.merge(child_report_sink)

    return report


def _check_child_has_export(child: dict[str, Any], *, prefix: str) -> ValidationReport:
    report = ValidationReport()
    export_nodes = [
        node
        for node in child.get("nodes") or []
        if str(node.get("node_id", "")).startswith(EXPORT_NODE_PREFIX)
    ]
    if not export_nodes:
        report.error(
            f"{prefix}子 DAG 没有跨域导出节点。"
            "只有 FileSaveStop / DataspaceFileSinkStop / LlmFileTransformStop 会写 "
            "final_output_path，缺了它远端 ResultResolver 会抛 RESULT_NOT_FOUND"
        )
        return report

    for node in export_nodes:
        skill_id = str((node.get("skill") or {}).get("skill_id", ""))
        if skill_id not in SINK_BUNDLES:
            report.error(
                f"{prefix}导出节点 {node.get('node_id')} 使用了 {skill_id}，"
                f"它不会写 final_output_path。必须是: {sorted(SINK_BUNDLES)}"
            )

    return report


def _duplicates(values: list[str]) -> set[str]:
    seen: set[str] = set()
    duplicated: set[str] = set()
    for value in values:
        if value in seen:
            duplicated.add(value)
        seen.add(value)
    return duplicated
