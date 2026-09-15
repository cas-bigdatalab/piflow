from __future__ import annotations

import json
from pathlib import Path

import pytest

from chemical.config import ChemicalConfig
from chemical.dag_scheduler import (
    CHEMICAL_REMOTE_PIPELINE_BUNDLE,
    schedule_chemical_dag,
    schedule_chemical_dag_file,
)


def _config() -> ChemicalConfig:
    return ChemicalConfig.from_mapping(
        {
            "main_node": {"ip": "10.0.0.1", "port": 50061},
            "nodes": [
                {
                    "name": "main",
                    "ip": "10.0.0.1",
                    "port": 50061,
                    "software": ["gaussian", "openbabel"],
                },
                {
                    "name": "remote",
                    "ip": "10.0.0.2",
                    "port": 50061,
                    "software": ["gaussian", "multiwfn"],
                },
            ],
        }
    )


def _node(skill_id: str, node_id: str = "node-1") -> dict:
    return {
        "node_id": node_id,
        "node_name": "计算节点",
        "skill": {"skill_id": skill_id},
        "input_params": [
            {"param_name": "input_path", "value_mode": "reference"},
            {"param_name": "method", "value_mode": "manual", "param_value": "demo"},
        ],
        "out_params": [{"param_name": "output_path", "param_type": "file"}],
    }


def test_scheduler_keeps_software_node_local_when_main_node_matches() -> None:
    dag = {"nodes": [_node("gaussian")], "bindings": []}

    plan = schedule_chemical_dag(
        dag,
        config=_config(),
        skill_json_resolver=lambda _: {"required_software": "gaussian"},
    )

    assert plan.dag_definition["nodes"][0] == dag["nodes"][0]
    assert plan.decisions[0].execution_target == "10.0.0.1:50061"
    assert plan.decisions[0].transformed is False


def test_scheduler_merges_software_from_nodes_with_same_main_ip() -> None:
    config = ChemicalConfig.from_mapping(
        {
            "main_node": {"ip": "10.0.0.1", "port": 50061},
            "nodes": [
                {
                    "name": "main-openbabel",
                    "ip": "10.0.0.1",
                    "port": 50061,
                    "software": ["openbabel"],
                },
                {
                    "name": "main-gaussian",
                    "ip": "10.0.0.1",
                    "port": 50062,
                    "software": ["gaussian"],
                },
                {
                    "name": "remote",
                    "ip": "10.0.0.2",
                    "port": 50061,
                    "software": ["multiwfn"],
                },
            ],
        }
    )
    dag = {"nodes": [_node("gaussian")], "bindings": []}

    plan = schedule_chemical_dag(
        dag,
        config=config,
        skill_json_resolver=lambda _: {"required_software": "gaussian"},
    )

    assert plan.dag_definition == dag
    assert plan.decisions[0].execution_target == "10.0.0.1:50061"
    assert plan.decisions[0].execution_node_name == "main_node"
    assert plan.decisions[0].transformed is False


def test_scheduler_only_uses_different_ip_nodes_as_remote_targets() -> None:
    config = ChemicalConfig.from_mapping(
        {
            "main_node": {"ip": "10.0.0.1", "port": 50061},
            "nodes": [
                {
                    "name": "main-gaussian",
                    "ip": "10.0.0.1",
                    "port": 50062,
                    "software": ["gaussian"],
                },
                {
                    "name": "remote",
                    "ip": "10.0.0.2",
                    "port": 50061,
                    "software": ["multiwfn"],
                },
            ],
        }
    )
    dag = {"nodes": [_node("multiwfn")], "bindings": []}

    plan = schedule_chemical_dag(
        dag,
        config=config,
        skill_json_resolver=lambda _: {"required_software": "multiwfn"},
    )

    assert plan.decisions[0].execution_node_name == "remote"
    assert plan.decisions[0].execution_target == "10.0.0.2:50061"


def test_scheduler_wraps_node_for_remote_execution() -> None:
    dag = {"nodes": [_node("multiwfn")], "bindings": []}

    plan = schedule_chemical_dag(
        dag,
        config=_config(),
        skill_json_resolver=lambda _: {"required_software": "multiwfn"},
    )

    scheduled_node = plan.dag_definition["nodes"][0]
    assert scheduled_node["skill"]["skill_id"] == CHEMICAL_REMOTE_PIPELINE_BUNDLE
    assert scheduled_node["input_params"][0]["param_name"] == "node_definition_json"
    assert scheduled_node["input_params"][1]["param_value"] == "10.0.0.2:50061"
    assert scheduled_node["input_params"][2]["param_value"] == "10.0.0.1:50061"
    assert scheduled_node["input_params"][0]["param_value"]["skill"]["skill_id"] == "multiwfn"
    assert scheduled_node["out_params"] == dag["nodes"][0]["out_params"]
    assert plan.decisions[0].transformed is True


def test_scheduler_does_not_transform_skill_without_required_software() -> None:
    dag = {"nodes": [_node("plain")], "bindings": []}

    plan = schedule_chemical_dag(
        dag,
        config=_config(),
        skill_json_resolver=lambda _: {"name": "plain skill"},
    )

    assert plan.dag_definition == dag
    assert plan.decisions[0].transformed is False


def test_scheduler_requires_all_software_on_one_node() -> None:
    dag = {"nodes": [_node("multiwfn")], "bindings": []}

    with pytest.raises(ValueError, match="openbabel, multiwfn"):
        schedule_chemical_dag(
            dag,
            config=_config(),
            skill_json_resolver=lambda _: {
                "required_software": ["openbabel", "multiwfn"]
            },
        )


def test_scheduler_accepts_resolver_with_absolute_skill_json_path(tmp_path: Path) -> None:
    skill_path = tmp_path / "skill.json"
    skill_path.write_text(
        json.dumps({"required_software": "multiwfn"}),
        encoding="utf-8",
    )
    dag = {"nodes": [_node(str(skill_path))], "bindings": []}

    plan = schedule_chemical_dag(
        dag,
        config=_config(),
        skill_json_resolver=lambda _: {"required_software": "multiwfn"},
    )

    embedded = plan.dag_definition["nodes"][0]["input_params"][0]["param_value"]
    assert embedded["skill"]["skill_id"] == str(skill_path)


def test_scheduler_can_load_dag_from_file(tmp_path: Path) -> None:
    dag_path = tmp_path / "dag.json"
    dag_path.write_text(
        json.dumps({"nodes": [_node("plain")], "bindings": []}),
        encoding="utf-8",
    )

    plan = schedule_chemical_dag_file(
        dag_path,
        config=_config(),
        skill_json_resolver=lambda _: {},
    )

    assert plan.dag_definition["nodes"][0]["node_id"] == "node-1"
