"""JSON codec for durable cross-DAG session snapshots.

The existing planning dataclasses intentionally remain unchanged.  This module
is the persistence boundary used only by the additive XDC session feature.
"""

from __future__ import annotations

from typing import Any

from .schema import (
    Binding,
    CrossDagPreBindPlan,
    DatasetCoverage,
    FacetCoverage,
    InputParam,
    IntentSpec,
    LogicalDag,
    LogicalNode,
    OutParam,
    RequirementFacet,
    SatisfactionReport,
    ValidationReport,
)

PRE_BIND_SCHEMA_VERSION = "1.0"


def encode_pre_bind_plan(plan: CrossDagPreBindPlan) -> dict[str, Any]:
    """Encode every field required to resume binding after a restart."""
    return {
        "schema_version": PRE_BIND_SCHEMA_VERSION,
        "plan_id": plan.plan_id,
        "mode": plan.mode,
        "intent": plan.intent.to_json(),
        "satisfaction": plan.satisfaction.to_json(),
        "logical_dag": plan.logical_dag.to_json(),
        "validation": plan.validation.to_json(),
        "planning_json": dict(plan.planning_json),
    }


def decode_pre_bind_plan(raw: dict[str, Any]) -> CrossDagPreBindPlan:
    """Restore a pre-bind plan without invoking intent or planning again."""
    version = str(raw.get("schema_version") or PRE_BIND_SCHEMA_VERSION)
    if version != PRE_BIND_SCHEMA_VERSION:
        raise ValueError(f"不支持的预绑定快照版本: {version}")

    return CrossDagPreBindPlan(
        plan_id=str(raw.get("plan_id") or ""),
        mode=str(raw.get("mode") or "composition"),
        intent=IntentSpec.from_json(dict(raw.get("intent") or {})),
        satisfaction=_decode_satisfaction(dict(raw.get("satisfaction") or {})),
        logical_dag=_decode_logical_dag(dict(raw.get("logical_dag") or {})),
        validation=_decode_validation(dict(raw.get("validation") or {})),
        planning_json=dict(raw.get("planning_json") or {}),
    )


def _decode_satisfaction(raw: dict[str, Any]) -> SatisfactionReport:
    coverages = []
    for coverage in raw.get("coverages") or []:
        facets = []
        for facet in coverage.get("facets") or []:
            facets.append(
                FacetCoverage(
                    key=str(facet.get("key") or ""),
                    label=str(facet.get("label") or ""),
                    mode=str(facet.get("mode") or "cover_all"),
                    required=[str(v) for v in facet.get("required") or []],
                    covered=[str(v) for v in facet.get("covered") or []],
                    missing=[str(v) for v in facet.get("missing") or []],
                    declared=bool(facet.get("declared", True)),
                )
            )
        coverages.append(
            DatasetCoverage(
                dataset_id=str(coverage.get("dataset_id") or ""),
                alias=str(coverage.get("alias") or ""),
                name=str(coverage.get("name") or ""),
                facets=facets,
                selected=bool(coverage.get("selected", True)),
            )
        )
    return SatisfactionReport(
        facets=[
            RequirementFacet.from_json(item) for item in raw.get("facets") or []
        ],
        coverages=coverages,
        mode=str(raw.get("mode") or "composition"),
        reason=str(raw.get("reason") or ""),
        notes=[str(v) for v in raw.get("notes") or []],
        scanned_count=int(raw.get("scanned_count") or 0),
    )


def _decode_logical_dag(raw: dict[str, Any]) -> LogicalDag:
    nodes = []
    for item in raw.get("nodes") or []:
        skill = dict(item.get("skill") or {})
        nodes.append(
            LogicalNode(
                node_id=str(item.get("node_id") or ""),
                node_name=str(item.get("node_name") or ""),
                skill_id=str(skill.get("skill_id") or ""),
                skill_name=str(skill.get("skill_name") or ""),
                node_type=str(item.get("node_type") or "default"),
                data_center=str(item.get("dataCenter") or ""),
                input_params=[
                    InputParam(
                        param_name=str(param.get("param_name") or ""),
                        value_mode=str(param.get("value_mode") or "manual"),
                        param_value=param.get("param_value", ""),
                        param_type=str(param.get("param_type") or "string"),
                        binding_id=str(param.get("binding_id") or ""),
                    )
                    for param in item.get("input_params") or []
                ],
                out_params=[
                    OutParam(
                        param_name=str(param.get("param_name") or ""),
                        param_type=str(param.get("param_type") or "file"),
                    )
                    for param in item.get("out_params") or []
                ],
                position={
                    str(key): float(value)
                    for key, value in (item.get("position") or {}).items()
                }
                or {"x": 0.0, "y": 0.0},
            )
        )
    return LogicalDag(
        task_id=str(raw.get("task_id") or ""),
        task_name=str(raw.get("task_name") or ""),
        description=str(raw.get("description") or ""),
        nodes=nodes,
        bindings=[
            Binding(
                from_node_id=str(item.get("from_node_id") or ""),
                from_param_name=str(item.get("from_param_name") or ""),
                to_node_id=str(item.get("to_node_id") or ""),
                to_param_name=str(item.get("to_param_name") or ""),
            )
            for item in raw.get("bindings") or []
        ],
    )


def _decode_validation(raw: dict[str, Any]) -> ValidationReport:
    return ValidationReport(
        errors=[str(v) for v in raw.get("errors") or []],
        warnings=[str(v) for v in raw.get("warnings") or []],
    )
