from __future__ import annotations

from runtime.cross_dag.config import CenterConfig, CrossDcConfig
from runtime.cross_dag.direct_executor import (
    DIRECT_RESULT_NODE_ID,
    DIRECT_SOURCE_NODE_ID,
    materialize_direct_access_plan,
    submit_direct_access_plan,
)
from runtime.cross_dag.registry_stub import (
    DataSourceRecord,
    DatasetRecord,
    ReplicaRecord,
    StubDatasourceRegistry,
)
from runtime.cross_dag.schema import (
    BindResult,
    CrossDagPlan,
    DirectAccess,
    IntentDataset,
    IntentSpec,
    LogicalDag,
    ReplicaCandidate,
    ReplicaDecision,
    SatisfactionReport,
    SegmentGraph,
    ValidationReport,
)
from runtime.distributed_dag_submitter import CrossDomainSubmitResult


def _direct_plan() -> tuple[CrossDagPlan, StubDatasourceRegistry, CrossDcConfig]:
    source_skill = (
        "piflow_engine.cn.piflow.engine.local.corpus_dataset_source_stop."
        "CorpusDatasetSourceStop"
    )
    dataset = IntentDataset(
        alias="quake",
        dataset_id="dataset-a",
        name="Earthquake catalog",
        locator="dataset-a",
        source_skill=source_skill,
        source_param="dataset_id",
        source_output_param="output",
        replicas=[
            ReplicaCandidate(
                replica_id="replica-a",
                source_id="center-a",
                center_id="center-a",
                locator="replica-dataset-a",
                metrics={"cpu_cores": 8, "memory_gb": 16},
            )
        ],
    )
    decision = ReplicaDecision(
        dataset_alias="quake",
        dataset_id="dataset-a",
        node_id="dataset-a",
        preferred_center_id="center-a",
        chosen=dataset.replicas[0],
        reason="same center, no cross-center transfer",
    )
    plan = CrossDagPlan(
        plan_id="xdc-direct-1",
        mode="direct",
        intent=IntentSpec(
            goal="Download the earthquake catalog",
            datasets=[dataset],
            output={"format": "txt", "name": "earthquake-catalog.txt"},
        ),
        satisfaction=SatisfactionReport(mode="direct", reason="one dataset matches"),
        logical_dag=LogicalDag(task_id="xdc-direct-1"),
        bind_result=BindResult(replica_decisions=[decision]),
        segment_graph=SegmentGraph(),
        nested_dsl={},
        validation=ValidationReport(),
        direct_access=DirectAccess(
            dataset_id="dataset-a",
            name="Earthquake catalog",
            alias="quake",
            replica_decision=decision,
        ),
    )
    registry = StubDatasourceRegistry(
        sources=(
            DataSourceRecord(
                ip="center-a",
                name="Center A",
                grpc_endpoint="center-a:50061",
            ),
        ),
        datasets=(
            DatasetRecord(
                dataset_id="dataset-a",
                name="Earthquake catalog",
                replicas=(
                    ReplicaRecord("replica-a", "center-a", "replica-dataset-a"),
                ),
                source_skill=source_skill,
                source_param="dataset_id",
                source_output_param="output",
            ),
        ),
    )
    config = CrossDcConfig(
        local_center_id="center-a",
        default_center_id="center-a",
        centers={
            "center-a": CenterConfig(
                center_id="center-a",
                center_name="Center A",
                grpc_endpoint="center-a:50061",
            )
        },
    )
    return plan, registry, config


def test_materialize_direct_plan_uses_selected_replica_and_registered_skill_id():
    plan, registry, config = _direct_plan()

    def resolve_skill(name: str) -> str:
        if name == "corpus_dataset_source_stop":
            return "corpus_dataset_source_stop_1.0.0"
        if name == "file_save_stop":
            return "file_save_stop_1.0.0"
        return name

    spec = materialize_direct_access_plan(
        plan,
        registry=registry,
        config=config,
        skill_resolver=resolve_skill,
    )

    assert spec.result_node_id == DIRECT_RESULT_NODE_ID
    assert spec.result_output_name == "output"
    assert plan.execution_center_id == "center-a"
    assert plan.execution_grpc_endpoint == "center-a:50061"
    assert plan.bind_result.center_of == {
        DIRECT_SOURCE_NODE_ID: "center-a",
        DIRECT_RESULT_NODE_ID: "center-a",
    }
    assert len(plan.execution_dsl["nodes"]) == 2
    source_node, save_node = plan.execution_dsl["nodes"]
    assert source_node["skill"] == {
        "skill_id": "corpus_dataset_source_stop_1.0.0",
        "skill_name": "corpus_dataset_source_stop",
    }
    assert source_node["input_params"][0]["param_value"] == "replica-dataset-a"
    assert source_node["out_params"] == [
        {"param_name": "output", "param_type": "file_artifact"}
    ]
    assert save_node["skill"] == {
        "skill_id": "file_save_stop_1.0.0",
        "skill_name": "file_save_stop",
    }
    assert save_node["input_params"] == [
        {
            "binding_id": "",
            "param_name": "absolute_path",
            "param_type": "string",
            "value_mode": "manual",
            "param_value": "/workspace/artifacts/xdc/xdc-direct-1/earthquake-catalog.txt",
            "value_source": "default",
        },
        {
            "binding_id": "",
            "param_name": "overwrite",
            "param_type": "string",
            "value_mode": "manual",
            "param_value": "true",
            "value_source": "default",
        },
    ]
    assert save_node["out_params"] == [
        {"param_name": "output", "param_type": "file_artifact"}
    ]
    assert plan.execution_dsl["edges"] == [
        {
            "edge_id": "edge-direct-dataset-source-direct-result-save",
            "from_node_id": DIRECT_SOURCE_NODE_ID,
            "to_node_id": DIRECT_RESULT_NODE_ID,
        }
    ]
    assert plan.execution_dsl["bindings"] == [
        {
            "binding_id": "direct-dataset-source:output->direct-result-save:output",
            "from_node_id": DIRECT_SOURCE_NODE_ID,
            "from_param_name": "output",
            "to_node_id": DIRECT_RESULT_NODE_ID,
            "to_param_name": "output",
        }
    ]
    assert plan.logical_dag.source_node_ids() == [DIRECT_SOURCE_NODE_ID]
    assert plan.logical_dag.sink_node_ids() == [DIRECT_RESULT_NODE_ID]


def test_submit_direct_plan_targets_selected_center_and_result_node():
    plan, registry, config = _direct_plan()
    captured = {}

    def submitter(definition, **kwargs):
        captured["definition"] = definition
        captured.update(kwargs)
        resource = kwargs["resource_resolver"](definition["nodes"][0])
        captured["resource"] = resource
        return CrossDomainSubmitResult(
            process_id="process-direct-1",
            status="SUBMITTED",
            execution_node_id="center-a",
            remote_grpc_target="center-a:50061",
            dag_definition=definition,
        )

    submission = submit_direct_access_plan(
        plan,
        registry=registry,
        config=config,
        skill_resolver=lambda name: name,
        submitter=submitter,
    )

    assert submission.result.process_id == "process-direct-1"
    assert submission.result_node_id == DIRECT_RESULT_NODE_ID
    assert submission.result_output_name == "output"
    assert captured["remote_grpc_target"] == "center-a:50061"
    assert captured["execution_node_id"] == "center-a"
    assert captured["remote_source_node_ids"] == {DIRECT_SOURCE_NODE_ID}
    assert captured["resource"].node_id == "center-a"
    assert captured["definition"]["task"]["dag_task_id"] == "xdc-direct-1"

    # The actual engine converter accepts the direct source-to-save DAG.
    from piflow_engine.cn.piflow.core.flow_bean import FlowBean
    from piflow_engine.cn.piflow.core.frontend_dag_converter import (
        convert_frontend_dag_to_piflow,
    )

    FlowBean.from_dict(
        convert_frontend_dag_to_piflow(captured["definition"])
    ).construct_flow()
