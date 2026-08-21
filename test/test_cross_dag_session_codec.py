from __future__ import annotations

from runtime.cross_dag.schema import (
    Binding,
    CrossDagPreBindPlan,
    DatasetCoverage,
    FacetCoverage,
    InputParam,
    IntentDataset,
    IntentSpec,
    LogicalDag,
    LogicalNode,
    OutParam,
    ReplicaCandidate,
    RequirementFacet,
    SatisfactionReport,
    ValidationReport,
)
from runtime.cross_dag.session_codec import decode_pre_bind_plan, encode_pre_bind_plan


def _pre_bind_plan() -> CrossDagPreBindPlan:
    requirement = RequirementFacet(
        key="field",
        label="领域",
        values=["地球科学"],
    )
    return CrossDagPreBindPlan(
        plan_id="xdc-persisted",
        mode="composition",
        intent=IntentSpec(
            goal="合并地球科学语料",
            user_request="合并三份资料",
            requirements=[requirement],
            datasets=[
                IntentDataset(
                    alias="quake",
                    dataset_id="dataset-quake",
                    source_id="center-a",
                    center_id="center-a",
                    locator="dataset-quake",
                    name="地震目录",
                    replicas=[
                        ReplicaCandidate(
                            replica_id="replica-a",
                            source_id="center-a",
                            center_id="center-a",
                            locator="dataset-quake",
                            metrics={"cpu_cores": 8},
                        )
                    ],
                    facets={"field": ["地球科学"]},
                    source_skill="corpus.source",
                    source_param="dataset_id",
                    source_output_param="output",
                )
            ],
        ),
        satisfaction=SatisfactionReport(
            facets=[requirement],
            coverages=[
                DatasetCoverage(
                    dataset_id="dataset-quake",
                    alias="quake",
                    name="地震目录",
                    facets=[
                        FacetCoverage(
                            key="field",
                            label="领域",
                            mode="cover_all",
                            required=["地球科学"],
                            covered=["地球科学"],
                        )
                    ],
                )
            ],
            mode="composition",
            reason="需要组配",
            scanned_count=3,
        ),
        logical_dag=LogicalDag(
            task_id="xdc-persisted",
            task_name="语料合并",
            nodes=[
                LogicalNode(
                    node_id="source",
                    node_name="source",
                    skill_id="skill-id",
                    skill_name="corpus_source",
                    data_center="center-a",
                    input_params=[
                        InputParam("dataset_id", param_value="dataset://dataset-quake")
                    ],
                    out_params=[OutParam("output", "file_artifact")],
                ),
                LogicalNode(
                    node_id="merge",
                    node_name="merge",
                    skill_id="merge-id",
                    skill_name="tar_merge",
                ),
            ],
            bindings=[Binding("source", "output", "merge", "data1")],
        ),
        validation=ValidationReport(warnings=["保守退化"]),
        planning_json={"task": {"name": "语料合并"}},
    )


def test_pre_bind_snapshot_round_trip_preserves_binding_inputs() -> None:
    encoded = encode_pre_bind_plan(_pre_bind_plan())
    restored = decode_pre_bind_plan(encoded)

    assert restored.plan_id == "xdc-persisted"
    assert restored.intent.datasets[0].replicas[0].replica_id == "replica-a"
    assert restored.logical_dag.nodes[0].data_center == "center-a"
    assert restored.logical_dag.bindings[0].binding_id == (
        "source:output->merge:data1"
    )
    assert restored.satisfaction.coverages[0].full_match is True
    assert restored.validation.warnings == ["保守退化"]
    assert encode_pre_bind_plan(restored) == encoded

