from __future__ import annotations

import json
import tarfile
from types import SimpleNamespace

from runtime.cross_dag.config import CrossDcConfig, resolve_cross_dc_config
from runtime.cross_dag.corpus_registry import _map_connector, _map_dataset
from runtime.cross_dag.engine import (
    finalize_cross_dag_pre_bind,
    plan_cross_dag,
    plan_cross_dag_pre_bind,
)
from runtime.cross_dag.executor import submit_cross_dag_plan
from runtime.cross_dag.intent import build_dataset_catalog
from runtime.cross_dag.registry_adapter import CallbackDatasourceRegistry
from runtime.cross_dag.registry_stub import (
    DatasetRecord,
    DataSourceRecord,
    ReplicaRecord,
    StubDatasourceRegistry,
)
from runtime.cross_dag.schema import IntentDataset, IntentSpec, ReplicaCandidate
from runtime.cross_dag.selector import select_replica
from runtime.cross_dag.validator import validate_nested_dsl
from runtime.remote_dag_scheduler import RemoteNodeResource, schedule_frontend_dag
from piflow_engine.cn.piflow.core.artifact import FileArtifact
from piflow_engine.cn.piflow.engine.local.tar_archive_merge_stop import TarArchiveMergeStop

CORPUS = (
    "piflow_engine.cn.piflow.engine.local.corpus_dataset_source_stop."
    "CorpusDatasetSourceStop"
)
TAR_MERGE = (
    "piflow_engine.cn.piflow.engine.local.tar_archive_merge_stop."
    "TarArchiveMergeStop"
)


def _registry() -> StubDatasourceRegistry:
    sources = (
        DataSourceRecord(
            ip="alpha.internal",
            source_id="connector-alpha",
            name="Alpha",
            grpc_endpoint="alpha.internal:61001",
            metrics={"cpu_cores": 8, "memory_gb": 16},
        ),
        DataSourceRecord(
            ip="beta.internal",
            source_id="connector-beta",
            name="Beta",
            grpc_endpoint="beta.internal:62002",
            metrics={"cpu_cores": 4, "memory_gb": 8},
        ),
    )
    datasets = (
        DatasetRecord(
            dataset_id="dynamic-a",
            name="A",
            replicas=(ReplicaRecord("rep-a", "alpha.internal", "dynamic-a"),),
            source_skill=CORPUS,
            source_param="dataset_id",
        ),
        DatasetRecord(
            dataset_id="dynamic-b",
            name="B",
            replicas=(ReplicaRecord("rep-b", "beta.internal", "dynamic-b"),),
            source_skill=CORPUS,
            source_param="dataset_id",
        ),
    )
    return StubDatasourceRegistry(sources=sources, datasets=datasets)


def _intent() -> IntentSpec:
    return IntentSpec(
        goal="merge dynamic corpus archives",
        datasets=[
            IntentDataset(
                alias="a",
                dataset_id="dynamic-a",
                name="A",
                replicas=[
                    ReplicaCandidate("rep-a", "alpha.internal", "alpha.internal", "dynamic-a")
                ],
                source_skill=CORPUS,
                source_param="dataset_id",
            ),
            IntentDataset(
                alias="b",
                dataset_id="dynamic-b",
                name="B",
                replicas=[
                    ReplicaCandidate("rep-b", "beta.internal", "beta.internal", "dynamic-b")
                ],
                source_skill=CORPUS,
                source_param="dataset_id",
            ),
        ],
        operations=[{"name": "tar merge"}],
    )


def _planning_json() -> dict:
    return {
        "task": {"name": "dynamic corpus tar"},
        "nodes": [
            {
                "node_name": "source-a",
                "skill_name": CORPUS,
                "params": {"dataset_id": "dataset://dynamic-a"},
            },
            {
                "node_name": "source-b",
                "skill_name": CORPUS,
                "params": {"dataset_id": "dataset://dynamic-b"},
            },
            {
                "node_name": "tar-merge",
                "skill_name": TAR_MERGE,
                "params": {
                    "data1": {"source_node": "source-a", "source_param": "output"},
                    "data2": {"source_node": "source-b", "source_param": "output"},
                    "output_file_name": "result.tar",
                },
            },
        ],
    }


def _planning_json_with_unstable_source_port() -> dict:
    planning = _planning_json()
    planning["nodes"][2]["params"]["data2"]["source_param"] = "file_2"
    return planning


def test_corpus_registry_normalizes_connector_reference_without_fixed_ips() -> None:
    sources = [
        {
            "connectorId": "connector-any",
            "connectorName": "Dynamic",
            "serverUrl": "http://node.example:7004/api",
            "grpcPort": 61234,
        }
    ]
    datasets = [
        {
            "datasetId": "dataset-any",
            "datasetName": "Dynamic dataset",
            "connectorId": "connector-any",
            "replicaId": "replica-any",
            "domain": "science;engineering",
        }
    ]
    registry = CallbackDatasourceRegistry(
        fetch_sources=lambda: sources,
        source_mapper=lambda raw: _map_connector(raw, grpc_port=50061, probe=False),
        fetch_datasets=lambda: datasets,
        dataset_mapper=lambda raw: _map_dataset(raw, facet_fields=("domain",)),
    )

    source = registry.list_sources()[0]
    dataset = registry.list_datasets()[0]
    assert source.source_id == "connector-any"
    assert source.center_id == "node.example"
    assert source.grpc_endpoint == "node.example:61234"
    assert dataset.replicas[0].source_ip == "node.example"
    assert dataset.replicas[0].replica_id == "replica-any"
    assert dataset.facets == {"domain": ("science", "engineering")}
    assert dataset.source_skill == CORPUS
    assert dataset.source_param == "dataset_id"

    catalog = build_dataset_catalog(registry)
    access = catalog[0]["读取契约"]
    assert access == {
        "skill_name": CORPUS,
        "param_name": "dataset_id",
        "param_value": "dataset://dataset-any",
        "output_param": "output",
    }


def test_corpus_registry_expands_multi_connector_dataset_into_replicas() -> None:
    sources = [
        {
            "connectorId": "DS-NODE-1",
            "serviceUrl": "10.0.82.213:7004",
        },
        {
            "connectorId": "DS-NODE-2",
            "serviceUrl": "10.0.90.174:7004",
        },
        {
            "connectorId": "DS-NODE-3",
            "serviceUrl": "10.0.90.94:7004",
        },
    ]
    datasets = [
        {
            "id": "6a6ab4da15840cf004056867",
            "title": "China land resources corpus",
            "cstr": "ES-CORPUS-K024",
            "connectorId": "DS-NODE-2,DS-NODE-1，DS-NODE-3;DS-NODE-2",
            "status": 9,
        }
    ]
    registry = CallbackDatasourceRegistry(
        fetch_sources=lambda: sources,
        source_mapper=lambda raw: _map_connector(raw, grpc_port=50061, probe=False),
        fetch_datasets=lambda: datasets,
        dataset_mapper=lambda raw: _map_dataset(raw, facet_fields=()),
    )

    dataset = registry.get_dataset("6a6ab4da15840cf004056867")

    assert dataset is not None
    assert [replica.replica_id for replica in dataset.replicas] == [
        "ES-CORPUS-K024@DS-NODE-2",
        "ES-CORPUS-K024@DS-NODE-1",
        "ES-CORPUS-K024@DS-NODE-3",
    ]
    assert [replica.source_ip for replica in dataset.replicas] == [
        "10.0.90.174",
        "10.0.82.213",
        "10.0.90.94",
    ]
    assert {replica.locator for replica in dataset.replicas} == {
        "6a6ab4da15840cf004056867"
    }
    intent_dataset = IntentDataset(
        alias="land",
        dataset_id=dataset.dataset_id,
        replicas=[
            ReplicaCandidate.from_json(replica.to_json())
            for replica in dataset.replicas
        ],
    )
    decision = select_replica(
        intent_dataset,
        preferred_center_id="10.0.90.174",
        known_centers={"10.0.82.213", "10.0.90.174", "10.0.90.94"},
        available_statuses={"AVAILABLE"},
    )
    assert decision.chosen is not None
    assert decision.chosen.center_id == "10.0.90.174"


def test_dynamic_registry_builds_topology_and_compiles_nested_plan() -> None:
    registry = _registry()
    base = CrossDcConfig(
        local_center_id="",
        default_center_id="",
        centers={},
        sink_skills=frozenset({TAR_MERGE}),
        available_statuses=frozenset({"AVAILABLE"}),
    )
    resolved = resolve_cross_dc_config(base, registry)
    assert set(resolved.centers) == {"alpha.internal", "beta.internal"}
    assert resolved.default_center_id == "alpha.internal"

    plan = plan_cross_dag(
        "merge them",
        registry=registry,
        config=base,
        intent=_intent(),
        planning_json=_planning_json(),
        skill_resolver=lambda name: name,
    )

    assert plan.validation.ok, plan.validation.errors
    assert plan.execution_center_id in resolved.centers
    assert plan.execution_grpc_endpoint == resolved.endpoint_of(plan.execution_center_id)
    assert len(plan.segment_graph.segments) == 2
    assert any(
        str(node.get("node_id", "")).startswith("remote-subdag-source-")
        for node in plan.nested_dsl["nodes"]
    )
    assert all(
        not str(node.get("node_id", "")).startswith("remote-subdag-source-")
        for node in plan.execution_dsl["nodes"]
    )


def test_pre_bind_phase_stops_before_replica_selection() -> None:
    registry = _registry()
    config = CrossDcConfig(
        local_center_id="",
        default_center_id="",
        centers={},
        sink_skills=frozenset({TAR_MERGE}),
        available_statuses=frozenset({"AVAILABLE"}),
    )
    events: list[str] = []

    pre_bind = plan_cross_dag_pre_bind(
        "merge them",
        registry=registry,
        config=config,
        intent=_intent(),
        planning_json=_planning_json(),
        skill_resolver=lambda name: name,
        on_stage=lambda stage, payload: events.append(
            f"{stage}:{payload.get('status', '')}"
        ),
    )

    assert pre_bind.validation.ok, pre_bind.validation.errors
    assert pre_bind.mode == "composition"
    assert all(node.data_center == "" for node in pre_bind.logical_dag.nodes)
    assert all(
        not node.to_dsl().get("dataCenter") for node in pre_bind.logical_dag.nodes
    )
    assert (
        pre_bind.logical_dag.node_map()["source-a"]
        .input_param("dataset_id")
        .param_value
        == "dataset://dynamic-a"
    )
    assert events == [
        "intent:started",
        "intent:finished",
        "satisfaction:started",
        "satisfaction:finished",
        "planning:started",
        "planning:finished",
        "expand:started",
        "expand:finished",
    ]


def test_finalize_pre_bind_binds_and_preserves_preview_snapshot() -> None:
    registry = _registry()
    base = CrossDcConfig(
        local_center_id="",
        default_center_id="",
        centers={},
        sink_skills=frozenset({TAR_MERGE}),
        available_statuses=frozenset({"AVAILABLE"}),
    )
    pre_bind = plan_cross_dag_pre_bind(
        "merge them",
        registry=registry,
        config=base,
        intent=_intent(),
        planning_json=_planning_json(),
        skill_resolver=lambda name: name,
    )
    events: list[str] = []

    plan = finalize_cross_dag_pre_bind(
        pre_bind,
        registry=registry,
        config=resolve_cross_dc_config(base, registry),
        on_stage=lambda stage, payload: events.append(
            f"{stage}:{payload.get('status', '')}"
        ),
    )

    assert plan.validation.ok, plan.validation.errors
    assert set(plan.bind_result.center_of.values()) == {
        "alpha.internal",
        "beta.internal",
    }
    assert {decision.dataset_id for decision in plan.bind_result.replica_decisions} == {
        "dynamic-a",
        "dynamic-b",
    }
    assert len(plan.segment_graph.segments) == 2
    assert all(node.data_center == "" for node in pre_bind.logical_dag.nodes)
    assert (
        pre_bind.logical_dag.node_map()["source-a"]
        .input_param("dataset_id")
        .param_value
        == "dataset://dynamic-a"
    )
    assert events == [
        "bind:started",
        "bind:finished",
        "segment:started",
        "segment:finished",
        "nest:started",
        "nest:finished",
        "validate:started",
        "validate:finished",
    ]


def test_registered_dataset_output_contract_overrides_planner_port() -> None:
    plan = plan_cross_dag(
        "merge them",
        registry=_registry(),
        config=CrossDcConfig(
            local_center_id="",
            default_center_id="",
            centers={},
            sink_skills=frozenset({TAR_MERGE}),
            available_statuses=frozenset({"AVAILABLE"}),
        ),
        intent=_intent(),
        planning_json=_planning_json_with_unstable_source_port(),
        skill_resolver=lambda name: name,
    )

    source_binding = next(
        binding
        for binding in plan.logical_dag.bindings
        if binding.from_node_id == "source-b"
    )
    assert source_binding.from_param_name == "output"
    merge = plan.logical_dag.node_map()["tar-merge"]
    assert merge.input_param("data2").binding_id == source_binding.binding_id
    assert plan.logical_dag.node_map()["source-b"].out_params[0].param_name == "output"
    assert any("注册契约" in warning for warning in plan.validation.warnings)

    remote_nodes = [
        node
        for node in plan.nested_dsl["nodes"]
        if str(node.get("node_id", "")).startswith("remote-subdag-source-")
    ]
    assert remote_nodes
    remote_params = {
        param["param_name"]: param["param_value"]
        for param in remote_nodes[0]["input_params"]
    }
    child = json.loads(remote_params["subdag_definition_json"])
    assert remote_params["result_node_id"] == "source-b"
    assert remote_params["result_output_name"] == "output"
    assert all(
        not str(node["node_id"]).startswith("__export__")
        for node in child["nodes"]
    )
    source = next(node for node in child["nodes"] if node["node_id"] == "source-b")
    assert source["out_params"] == [
        {"param_name": "output", "param_type": "file_artifact"}
    ]


def test_flat_dag_matches_execution_engine_parameter_contract() -> None:
    plan = plan_cross_dag(
        "merge them",
        registry=_registry(),
        config=CrossDcConfig(
            local_center_id="",
            default_center_id="",
            centers={},
            sink_skills=frozenset({TAR_MERGE}),
            available_statuses=frozenset({"AVAILABLE"}),
        ),
        intent=_intent(),
        planning_json=_planning_json(),
        skill_resolver=lambda name: name,
    )

    assert set(plan.execution_dsl) == {"task", "nodes", "edges", "bindings"}
    assert {node["node_id"] for node in plan.execution_dsl["nodes"]} == {
        "source-a",
        "source-b",
        "tar-merge",
    }
    for node in plan.execution_dsl["nodes"]:
        assert set(node) == {
            "node_id",
            "node_name",
            "skill",
            "input_params",
            "out_params",
        }
        assert all(
            param["value_mode"] == "manual"
            and param["value_source"] == "default"
            for param in node["input_params"]
        )
        assert all(
            param["param_type"] != "file" for param in node["out_params"]
        )

    merge = next(
        node for node in plan.execution_dsl["nodes"] if node["node_id"] == "tar-merge"
    )
    assert [param["param_name"] for param in merge["input_params"]] == [
        "output_file_name"
    ]
    assert merge["out_params"] == [
        {"param_name": "output", "param_type": "file_artifact"}
    ]


def test_each_new_plan_refreshes_dynamic_registry_snapshot() -> None:
    registry = _registry()
    refresh_calls: list[str] = []
    registry.refresh = lambda: refresh_calls.append("refresh")  # type: ignore[attr-defined]
    config = CrossDcConfig(
        local_center_id="",
        default_center_id="",
        centers={},
        sink_skills=frozenset({TAR_MERGE}),
        available_statuses=frozenset({"AVAILABLE"}),
    )

    plan_cross_dag(
        "merge them",
        registry=registry,
        config=config,
        intent=_intent(),
        planning_json=_planning_json(),
        skill_resolver=lambda name: name,
    )

    assert refresh_calls == ["refresh"]


def test_compiled_plan_submits_flat_execution_dsl(monkeypatch) -> None:
    registry = _registry()
    config = CrossDcConfig(
        local_center_id="",
        default_center_id="",
        centers={},
        sink_skills=frozenset({TAR_MERGE}),
        available_statuses=frozenset({"AVAILABLE"}),
    )
    plan = plan_cross_dag(
        "merge them",
        registry=registry,
        config=config,
        intent=_intent(),
        planning_json=_planning_json(),
        skill_resolver=lambda name: name,
    )

    calls = []

    def submit(definition_json: dict, **kwargs):
        calls.append((definition_json, kwargs))
        return SimpleNamespace(
            process_id="run-123",
            status="SUBMITTED",
            execution_node_id=kwargs["execution_node_id"],
        )

    monkeypatch.setattr(
        "runtime.cross_dag.executor.submit_cross_domain_dag",
        submit,
    )
    result = submit_cross_dag_plan(plan)

    assert result.process_id == "run-123"
    assert result.execution_node_id == plan.execution_center_id
    assert calls[0][0] == plan.execution_dsl
    assert calls[0][1]["remote_grpc_target"] == plan.execution_grpc_endpoint
    assert set(calls[0][1]["remote_source_node_ids"]) == {"source-a", "source-b"}


def test_plan_submission_schedules_with_bound_registry_resources(monkeypatch) -> None:
    plan = plan_cross_dag(
        "merge them",
        registry=_registry(),
        config=CrossDcConfig(
            local_center_id="",
            default_center_id="",
            centers={},
            sink_skills=frozenset({TAR_MERGE}),
            available_statuses=frozenset({"AVAILABLE"}),
        ),
        intent=_intent(),
        planning_json=_planning_json(),
        skill_resolver=lambda name: name,
    )
    submitted = []

    class Client:
        def __init__(self, target: str):
            assert target == plan.execution_grpc_endpoint

        def submit_remote_root_dag(self, payload: str):
            submitted.append(json.loads(payload))
            return SimpleNamespace(run_id="run-456", status="SUBMITTED")

        def close(self) -> None:
            pass

    monkeypatch.setattr(
        "runtime.distributed_dag_submitter.create_remote_execution_client",
        Client,
    )
    result = submit_cross_dag_plan(plan)

    assert result.process_id == "run-456"
    scheduled_node_ids = {node["node_id"] for node in submitted[0]["nodes"]}
    assert "source-a" in scheduled_node_ids
    assert "source-b" not in scheduled_node_ids
    assert "remote-subdag-source-source-b" in scheduled_node_ids


def test_flat_corpus_scheduler_does_not_require_duplicate_node_id_param() -> None:
    dag = {
        "task": {"dag_task_id": "flat-demo", "dag_task_name": "flat demo"},
        "nodes": [
            {
                "node_id": "corpus-a",
                "skill": {"skill_id": CORPUS},
                "input_params": [
                    {"param_name": "dataset_id", "param_value": "dynamic-a"}
                ],
            },
            {
                "node_id": "corpus-b",
                "skill": {"skill_id": CORPUS},
                "input_params": [
                    {"param_name": "dataset_id", "param_value": "dynamic-b"}
                ],
            },
            {"node_id": "merge", "skill": {"skill_id": TAR_MERGE}},
        ],
        "edges": [
            {"from_node_id": "corpus-a", "to_node_id": "merge"},
            {"from_node_id": "corpus-b", "to_node_id": "merge"},
        ],
        "bindings": [
            {
                "from_node_id": "corpus-a",
                "from_param_name": "output",
                "to_node_id": "merge",
                "to_param_name": "data1",
            },
            {
                "from_node_id": "corpus-b",
                "from_param_name": "output",
                "to_node_id": "merge",
                "to_param_name": "data2",
            },
        ],
    }

    def resolve(node: dict) -> RemoteNodeResource:
        dataset_id = node["input_params"][0]["param_value"]
        if dataset_id == "dynamic-a":
            return RemoteNodeResource("connector-alpha", 8, 16, 100, "alpha:50061")
        return RemoteNodeResource("connector-beta", 4, 8, 100, "beta:50061")

    scheduled = schedule_frontend_dag(
        dag,
        execution_node_id="connector-alpha",
        resource_resolver=resolve,
    )
    node_ids = {node["node_id"] for node in scheduled.dag_definition["nodes"]}
    assert "corpus-a" in node_ids
    assert "corpus-b" not in node_ids
    assert "remote-subdag-source-corpus-b" in node_ids
    assert validate_nested_dsl(scheduled.dag_definition).ok


def test_tar_archive_merge_stop_merges_arbitrary_input_ports(tmp_path) -> None:
    archives = []
    for index in (1, 2):
        source_file = tmp_path / f"source-{index}.txt"
        source_file.write_text(f"value-{index}", encoding="utf-8")
        archive_path = tmp_path / f"source-{index}.tar"
        with tarfile.open(archive_path, "w") as archive:
            archive.add(source_file, arcname=source_file.name)
        archives.append(archive_path)

    class Inputs:
        def ports(self):
            return ["data2", "data1"]

        def read(self, port):
            index = 0 if port == "data1" else 1
            return FileArtifact(path=str(archives[index]))

    class Outputs:
        artifact = None

        def write(self, artifact, port="output"):
            assert port == "output"
            self.artifact = artifact

    process = SimpleNamespace(pid=lambda: "process-1")
    process_context = SimpleNamespace(get_process=lambda: process)
    stop_job = SimpleNamespace(get_stop_name=lambda: "tar-merge", jid=lambda: "job-1")
    job_context = SimpleNamespace(
        get_process_context=lambda: process_context,
        get_stop_job=lambda: stop_job,
        put=lambda key, value: None,
    )
    process_config = SimpleNamespace(
        get=lambda key, default=None: str(tmp_path)
    )

    stop = TarArchiveMergeStop()
    stop.set_properties({"output_file_name": "combined.tar"})
    stop.initialize(process_config)
    outputs = Outputs()
    stop.perform(Inputs(), outputs, job_context)

    assert outputs.artifact is not None
    with tarfile.open(outputs.artifact.path, "r") as archive:
        assert archive.getnames() == ["source-1.txt", "source-2.txt"]
