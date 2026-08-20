from __future__ import annotations

import json
import tarfile
from types import SimpleNamespace

from runtime.cross_dag.config import CrossDcConfig, resolve_cross_dc_config
from runtime.cross_dag.corpus_registry import _map_connector, _map_dataset
from runtime.cross_dag.engine import plan_cross_dag
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
        str(node.get("node_id", "")).startswith("__remote__")
        for node in plan.nested_dsl["nodes"]
    )


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
        if str(node.get("node_id", "")).startswith("__remote__")
    ]
    assert remote_nodes
    child_json = next(
        param["param_value"]
        for param in remote_nodes[0]["input_params"]
        if param["param_name"] == "subdag_definition_json"
    )
    child = json.loads(child_json)
    export_binding = next(
        binding
        for binding in child["bindings"]
        if str(binding["to_node_id"]).startswith("__export__")
    )
    assert export_binding["from_param_name"] == "output"


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


def test_compiled_plan_submits_directly_to_its_root_endpoint(monkeypatch) -> None:
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

    class Client:
        def __init__(self, target: str):
            calls.append(("target", target))

        def submit_remote_root_dag(self, payload: str):
            calls.append(("payload", json.loads(payload)))
            return SimpleNamespace(run_id="run-123", status="SUBMITTED")

        def close(self) -> None:
            calls.append(("closed", True))

    monkeypatch.setattr(
        "runtime.distributed_dag_submitter.create_remote_execution_client",
        Client,
    )
    result = submit_cross_dag_plan(plan)

    assert result.process_id == "run-123"
    assert result.execution_node_id == plan.execution_center_id
    assert calls[0] == ("target", plan.execution_grpc_endpoint)
    assert calls[1][1] == plan.nested_dsl


def test_flat_corpus_scheduler_does_not_require_duplicate_node_id_param() -> None:
    dag = {
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
