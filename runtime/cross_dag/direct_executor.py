"""Session-only execution support for direct-access cross-DAG plans.

The ordinary direct-access API intentionally returns a replica route without
submitting a DAG.  Session tasks need a real process and downloadable result,
so this module materializes that route as a data-source node followed by a
stable result-save node and submits it through the existing distributed
execution entry point.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Callable

from runtime.distributed_dag_submitter import (
    CrossDomainSubmitResult,
    submit_cross_domain_dag,
)
from runtime.remote_dag_scheduler import RemoteNodeResource

from .config import CrossDcConfig, get_cross_dc_config, resolve_cross_dc_config
from .planner_bridge import SkillResolver, database_skill_resolver
from .registry_stub import DatasourceRegistry, get_registry
from .schema import (
    BUNDLE_FILE_SAVE,
    FILE_SAVE_INPUT_PORT,
    MODE_DIRECT,
    BindResult,
    Binding,
    CrossDagError,
    CrossDagPlan,
    InputParam,
    IntentDataset,
    LogicalDag,
    LogicalNode,
    OutParam,
    ReplicaCandidate,
    Segment,
    SegmentGraph,
    build_execution_dsl,
)


DIRECT_SOURCE_NODE_ID = "direct-dataset-source"
DIRECT_RESULT_NODE_ID = "direct-result-save"
DIRECT_RESULT_OUTPUT_NAME = "output"


@dataclass(frozen=True)
class DirectExecutionSpec:
    """The materialized DAG and the output selector used by result APIs."""

    result_node_id: str
    result_output_name: str


@dataclass(frozen=True)
class DirectExecutionSubmission:
    """A submitted direct run plus its deterministic result selector."""

    result: CrossDomainSubmitResult
    result_node_id: str
    result_output_name: str


def materialize_direct_access_plan(
    plan: CrossDagPlan,
    *,
    registry: DatasourceRegistry | None = None,
    config: CrossDcConfig | None = None,
    skill_resolver: SkillResolver | None = None,
) -> DirectExecutionSpec:
    """Attach an executable, downloadable DAG to an already bound direct plan."""
    if plan.mode != MODE_DIRECT:
        raise CrossDagError("only direct plans can be materialized as direct runs")

    access = plan.direct_access
    decision = access.replica_decision if access is not None else None
    chosen = decision.chosen if decision is not None else None
    if access is None or decision is None or chosen is None:
        raise CrossDagError("direct plan is missing its selected dataset replica")

    resolved_registry = registry or get_registry()
    resolved_config = resolve_cross_dc_config(
        config or get_cross_dc_config(),
        resolved_registry,
    )
    dataset = _resolve_dataset(plan, access.dataset_id, resolved_registry)

    source_skill = str(dataset.source_skill or "").strip()
    source_param = str(dataset.source_param or "").strip()
    source_output_param = str(dataset.source_output_param or "").strip()
    locator = str(chosen.locator or dataset.locator or "").strip()
    center_id = str(chosen.center_id or "").strip()
    if not source_skill or not source_param or not source_output_param:
        raise CrossDagError(
            f"dataset {access.dataset_id} has an incomplete access contract"
        )
    if not locator:
        raise CrossDagError(
            f"selected replica {chosen.replica_id} has no access locator"
        )
    if not center_id:
        raise CrossDagError(
            f"selected replica {chosen.replica_id} has no execution center"
        )
    try:
        endpoint = resolved_config.endpoint_of(center_id)
    except KeyError as exc:
        raise CrossDagError(str(exc)) from exc

    resolver = skill_resolver or database_skill_resolver()
    source_skill_name = _canonical_skill_name(source_skill)
    source_skill_id = _resolve_source_skill_id(
        source_skill,
        skill_name=source_skill_name,
        resolver=resolver,
    )
    source_node = LogicalNode(
        node_id=DIRECT_SOURCE_NODE_ID,
        node_name="direct_dataset_source",
        skill_id=source_skill_id,
        skill_name=source_skill_name,
        input_params=[
            InputParam(
                param_name=source_param,
                param_type="string",
                value_mode="manual",
                param_value=locator,
            )
        ],
        out_params=[OutParam(param_name=source_output_param, param_type="file")],
    )
    save_skill_name = _canonical_skill_name(BUNDLE_FILE_SAVE)
    save_node = LogicalNode(
        node_id=DIRECT_RESULT_NODE_ID,
        node_name="direct_result_save",
        skill_id=_resolve_source_skill_id(
            BUNDLE_FILE_SAVE,
            skill_name=save_skill_name,
            resolver=resolver,
        ),
        skill_name=save_skill_name,
        input_params=[
            InputParam(
                param_name="absolute_path",
                param_type="string",
                value_mode="manual",
                param_value=_direct_result_path(
                    export_dir=resolved_config.export_dir,
                    plan_id=plan.plan_id,
                    output=plan.intent.output,
                    dataset_id=access.dataset_id,
                ),
            ),
            InputParam(
                param_name="overwrite",
                param_type="string",
                value_mode="manual",
                param_value="true",
            ),
        ],
        out_params=[
            OutParam(param_name=DIRECT_RESULT_OUTPUT_NAME, param_type="file")
        ],
    )
    result_binding = Binding(
        from_node_id=DIRECT_SOURCE_NODE_ID,
        from_param_name=source_output_param,
        to_node_id=DIRECT_RESULT_NODE_ID,
        to_param_name=FILE_SAVE_INPUT_PORT,
    )
    task_name = plan.intent.goal or access.name or "Direct dataset access"
    logical_dag = LogicalDag(
        task_id=plan.plan_id,
        task_name=task_name,
        description=f"Access dataset {access.dataset_id} from replica {chosen.replica_id}",
        nodes=[source_node, save_node],
        bindings=[result_binding],
    )
    execution_dsl = build_execution_dsl(
        logical_dag,
        task_id=plan.plan_id,
        task_name=task_name,
    )
    segment_id = f"{center_id}#direct"
    endpoints = {
        known_center_id: center.grpc_endpoint
        for known_center_id, center in resolved_config.centers.items()
    }

    # Only direct plans reach this code path.  Composition plans continue to
    # use their existing bind/segment/nest products unchanged.
    plan.logical_dag = logical_dag
    plan.execution_dsl = execution_dsl
    plan.nested_dsl = execution_dsl
    plan.execution_center_id = center_id
    plan.execution_grpc_endpoint = endpoint
    plan.center_endpoints = endpoints
    plan.bind_result = BindResult(
        center_of={
            DIRECT_SOURCE_NODE_ID: center_id,
            DIRECT_RESULT_NODE_ID: center_id,
        },
        reasons={
            DIRECT_SOURCE_NODE_ID: decision.reason,
            DIRECT_RESULT_NODE_ID: "与数据源在同一中心保存最终结果",
        },
        replica_decisions=list(plan.bind_result.replica_decisions),
    )
    plan.segment_graph = SegmentGraph(
        segments={
            segment_id: Segment(
                segment_id=segment_id,
                center_id=center_id,
                level=0,
                node_ids=[DIRECT_SOURCE_NODE_ID, DIRECT_RESULT_NODE_ID],
            )
        },
        segment_of={
            DIRECT_SOURCE_NODE_ID: segment_id,
            DIRECT_RESULT_NODE_ID: segment_id,
        },
        levels={segment_id: 0},
    )

    return DirectExecutionSpec(
        result_node_id=DIRECT_RESULT_NODE_ID,
        result_output_name=DIRECT_RESULT_OUTPUT_NAME,
    )


def submit_direct_access_plan(
    plan: CrossDagPlan,
    *,
    registry: DatasourceRegistry | None = None,
    config: CrossDcConfig | None = None,
    skill_resolver: SkillResolver | None = None,
    submitter: Callable[..., CrossDomainSubmitResult] | None = None,
) -> DirectExecutionSubmission:
    """Materialize and submit a direct plan without changing composition code."""
    spec = materialize_direct_access_plan(
        plan,
        registry=registry,
        config=config,
        skill_resolver=skill_resolver,
    )
    access = plan.direct_access
    decision = access.replica_decision if access is not None else None
    chosen = decision.chosen if decision is not None else None
    if chosen is None:  # guarded above, retained for type/runtime safety
        raise CrossDagError("direct plan is missing its selected replica")

    def resolve(_: dict[str, Any]) -> RemoteNodeResource:
        metrics = chosen.metrics or {}
        return RemoteNodeResource(
            node_id=plan.execution_center_id,
            cpu_cores=float(metrics.get("cpu_cores", 0.0) or 0.0),
            memory_gb=float(metrics.get("memory_gb", 0.0) or 0.0),
            free_disk_gb=float(metrics.get("free_disk_gb", 0.0) or 0.0),
            remote_grpc_target=plan.execution_grpc_endpoint,
        )

    execute = submitter or submit_cross_domain_dag
    result = execute(
        plan.execution_dsl,
        remote_grpc_target=plan.execution_grpc_endpoint,
        execution_node_id=plan.execution_center_id,
        resource_resolver=resolve,
        remote_source_node_ids={DIRECT_SOURCE_NODE_ID},
    )
    return DirectExecutionSubmission(
        result=result,
        result_node_id=spec.result_node_id,
        result_output_name=spec.result_output_name,
    )


def _resolve_dataset(
    plan: CrossDagPlan,
    dataset_id: str,
    registry: DatasourceRegistry,
) -> IntentDataset:
    for dataset in plan.intent.datasets:
        if dataset.dataset_id == dataset_id:
            return dataset

    record = registry.get_dataset(dataset_id)
    if record is None:
        raise CrossDagError(f"direct dataset is no longer registered: {dataset_id}")
    dataset = IntentDataset(
        alias=dataset_id,
        dataset_id=record.dataset_id,
        source_id=record.source_id,
        center_id=record.center_id,
        locator=record.locator,
        name=record.name,
        replicas=[
            ReplicaCandidate.from_json(replica.to_json())
            for replica in record.replicas
        ],
        facets={
            str(key): [str(value) for value in values]
            for key, values in (record.facets or {}).items()
        },
        source_skill=record.source_skill,
        source_param=record.source_param,
        source_output_param=record.source_output_param,
    )
    # A direct full match may have been found by scanning the full registry
    # instead of by the intent model.  Add it to this direct plan so the same
    # frontend `sources` projection works after materialization.
    plan.intent.datasets.append(dataset)
    return dataset


def _canonical_skill_name(source_skill: str) -> str:
    leaf = str(source_skill or "").rsplit(".", 1)[-1]
    if "_" in leaf:
        return leaf
    return re.sub(r"(?<!^)(?=[A-Z])", "_", leaf).lower()


def _resolve_source_skill_id(
    source_skill: str,
    *,
    skill_name: str,
    resolver: SkillResolver,
) -> str:
    """Prefer the registered skill_id while retaining class-path fallback."""
    leaf = source_skill.rsplit(".", 1)[-1]
    for candidate in dict.fromkeys((source_skill, leaf, skill_name)):
        resolved = str(resolver(candidate) or "").strip()
        if resolved and resolved != candidate:
            return resolved
    return str(resolver(source_skill) or source_skill)


def _direct_result_path(
    *,
    export_dir: str,
    plan_id: str,
    output: dict[str, Any],
    dataset_id: str,
) -> str:
    """Build a stable per-plan path for the direct result artifact."""
    raw_name = str((output or {}).get("name") or "").strip()
    raw_format = str((output or {}).get("format") or "").strip().lstrip(".")
    fallback = f"{dataset_id}.{raw_format}" if raw_format else f"{dataset_id}.data"

    file_name = raw_name.replace("\\", "/").rsplit("/", 1)[-1]
    file_name = re.sub(r'[\x00-\x1f<>:"/\\|?*]', "_", file_name).strip(" .")
    if not file_name:
        file_name = fallback

    base = str(export_dir or "/workspace/artifacts/xdc").strip().rstrip("/\\")
    return f"{base}/{plan_id}/{file_name}"
