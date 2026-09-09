from __future__ import annotations

import json

from runtime.remote_dag_scheduler import schedule_frontend_dag


def test_schedule_frontend_dag_rewrites_remote_branch_into_remote_subdag_source():
    dag_definition = {
        "task": {
            "dag_task_id": "dag-1",
            "dag_task_name": "cross domain demo",
        },
        "nodes": [
            {
                "node_id": "A",
                "node_name": "A source",
                "skill": {
                    "skill_id": "piflow_engine.cn.piflow.engine.local.remote_source_stop.RemoteSourceStop",
                    "skill_name": "remote_source_stop",
                },
                "input_params": [
                    {
                        "param_name": "file_path",
                        "param_value": "/data/a.csv",
                        "value_mode": "manual",
                    },
                    {
                        "param_name": "node_id",
                        "param_value": "10.0.0.1",
                        "value_mode": "manual",
                    },
                    {
                        "param_name": "remote_grpc_target",
                        "param_value": "10.0.0.1:50061",
                        "value_mode": "manual",
                    },
                    {
                        "param_name": "cpu_cores",
                        "param_value": "4",
                        "value_mode": "manual",
                    },
                    {
                        "param_name": "memory_gb",
                        "param_value": "16",
                        "value_mode": "manual",
                    },
                    {
                        "param_name": "free_disk_gb",
                        "param_value": "100",
                        "value_mode": "manual",
                    },
                ],
                "out_params": [{"param_name": "output", "param_type": "file"}],
            },
            {
                "node_id": "B",
                "node_name": "B source",
                "skill": {
                    "skill_id": "piflow_engine.cn.piflow.engine.local.remote_source_stop.RemoteSourceStop",
                    "skill_name": "remote_source_stop",
                },
                "input_params": [
                    {
                        "param_name": "file_path",
                        "param_value": "/data/b.csv",
                        "value_mode": "manual",
                    },
                    {
                        "param_name": "node_id",
                        "param_value": "10.0.0.2",
                        "value_mode": "manual",
                    },
                    {
                        "param_name": "remote_grpc_target",
                        "param_value": "10.0.0.2:50061",
                        "value_mode": "manual",
                    },
                    {
                        "param_name": "cpu_cores",
                        "param_value": "8",
                        "value_mode": "manual",
                    },
                    {
                        "param_name": "memory_gb",
                        "param_value": "32",
                        "value_mode": "manual",
                    },
                    {
                        "param_name": "free_disk_gb",
                        "param_value": "500",
                        "value_mode": "manual",
                    },
                ],
                "out_params": [{"param_name": "output", "param_type": "file"}],
            },
            {
                "node_id": "C",
                "node_name": "C transform",
                "skill": {
                    "skill_id": "/tmp/c.json",
                    "skill_name": "c_transform",
                },
                "input_params": [],
                "out_params": [{"param_name": "output", "param_type": "file"}],
            },
            {
                "node_id": "D",
                "node_name": "D merge",
                "skill": {
                    "skill_id": "/tmp/d.json",
                    "skill_name": "d_merge",
                },
                "input_params": [],
                "out_params": [{"param_name": "output", "param_type": "file"}],
            },
        ],
        "edges": [
            {"edge_id": "e1", "from_node_id": "A", "to_node_id": "D"},
            {"edge_id": "e2", "from_node_id": "B", "to_node_id": "C"},
            {"edge_id": "e3", "from_node_id": "C", "to_node_id": "D"},
        ],
        "bindings": [
            {"binding_id": "b1", "from_node_id": "A", "from_param_name": "output", "to_node_id": "D", "to_param_name": "left"},
            {"binding_id": "b2", "from_node_id": "B", "from_param_name": "output", "to_node_id": "C", "to_param_name": "input"},
            {"binding_id": "b3", "from_node_id": "C", "from_param_name": "output", "to_node_id": "D", "to_param_name": "right"},
        ],
    }

    plan = schedule_frontend_dag(dag_definition, execution_node_id="10.0.0.1")

    assert plan.execution_node_id == "10.0.0.1"
    node_ids = {node["node_id"] for node in plan.dag_definition["nodes"]}
    assert "A" in node_ids
    assert "D" in node_ids
    assert "B" not in node_ids
    assert "C" not in node_ids

    synthetic_nodes = [
        node for node in plan.dag_definition["nodes"] if node["skill"]["skill_name"] == "remoteSubDagSourceNode"
    ]
    assert len(synthetic_nodes) == 1
    synthetic = synthetic_nodes[0]
    assert synthetic["skill"]["skill_id"] == (
        "piflow_engine.cn.piflow.engine.local.remote_subdag_source_stop.RemoteSubDagSourceStop"
    )

    params = {item["param_name"]: item["param_value"] for item in synthetic["input_params"]}
    assert params["remote_grpc_target"] == "10.0.0.2:50061"
    subdag = json.loads(params["subdag_definition_json"])
    subdag_node_ids = {node["node_id"] for node in subdag["nodes"]}
    assert subdag_node_ids == {"B", "C"}

    bindings = plan.dag_definition["bindings"]
    assert any(
        binding["from_node_id"] == synthetic["node_id"]
        and binding["to_node_id"] == "D"
        and binding["to_param_name"] == "right"
        for binding in bindings
    )


def test_schedule_frontend_dag_selects_highest_resource_remote_node_when_not_explicitly_set():
    dag_definition = {
        "task": {
            "dag_task_id": "dag-1",
            "dag_task_name": "cross domain demo",
        },
        "nodes": [
            {
                "node_id": "A",
                "node_name": "A source",
                "skill": {
                    "skill_id": "piflow_engine.cn.piflow.engine.local.remote_source_stop.RemoteSourceStop",
                    "skill_name": "remote_source_stop",
                },
                "input_params": [
                    {
                        "param_name": "file_path",
                        "param_value": "/data/a.csv",
                        "value_mode": "manual",
                    },
                    {
                        "param_name": "node_id",
                        "param_value": "10.0.0.1",
                        "value_mode": "manual",
                    },
                    {
                        "param_name": "remote_grpc_target",
                        "param_value": "10.0.0.1:50061",
                        "value_mode": "manual",
                    },
                    {
                        "param_name": "cpu_cores",
                        "param_value": "4",
                        "value_mode": "manual",
                    },
                    {
                        "param_name": "memory_gb",
                        "param_value": "16",
                        "value_mode": "manual",
                    },
                    {
                        "param_name": "free_disk_gb",
                        "param_value": "100",
                        "value_mode": "manual",
                    },
                ],
                "out_params": [{"param_name": "output", "param_type": "file"}],
            },
            {
                "node_id": "B",
                "node_name": "B source",
                "skill": {
                    "skill_id": "piflow_engine.cn.piflow.engine.local.remote_source_stop.RemoteSourceStop",
                    "skill_name": "remote_source_stop",
                },
                "input_params": [
                    {
                        "param_name": "file_path",
                        "param_value": "/data/b.csv",
                        "value_mode": "manual",
                    },
                    {
                        "param_name": "node_id",
                        "param_value": "10.0.0.2",
                        "value_mode": "manual",
                    },
                    {
                        "param_name": "remote_grpc_target",
                        "param_value": "10.0.0.2:50061",
                        "value_mode": "manual",
                    },
                    {
                        "param_name": "cpu_cores",
                        "param_value": "8",
                        "value_mode": "manual",
                    },
                    {
                        "param_name": "memory_gb",
                        "param_value": "32",
                        "value_mode": "manual",
                    },
                    {
                        "param_name": "free_disk_gb",
                        "param_value": "500",
                        "value_mode": "manual",
                    },
                ],
                "out_params": [{"param_name": "output", "param_type": "file"}],
            },
            {
                "node_id": "C",
                "node_name": "C transform",
                "skill": {
                    "skill_id": "/tmp/c.json",
                    "skill_name": "c_transform",
                },
                "input_params": [],
                "out_params": [{"param_name": "output", "param_type": "file"}],
            },
        ],
        "edges": [
            {"edge_id": "e1", "from_node_id": "A", "to_node_id": "C"},
            {"edge_id": "e2", "from_node_id": "B", "to_node_id": "C"},
        ],
        "bindings": [
            {"binding_id": "b1", "from_node_id": "A", "from_param_name": "output", "to_node_id": "C", "to_param_name": "left"},
            {"binding_id": "b2", "from_node_id": "B", "from_param_name": "output", "to_node_id": "C", "to_param_name": "right"},
        ],
    }

    plan = schedule_frontend_dag(dag_definition, random_seed=7)

    assert plan.execution_node_id == "10.0.0.2"


def test_schedule_frontend_dag_uses_custom_resource_resolver():
    dag_definition = {
        "task": {
            "dag_task_id": "dag-1",
            "dag_task_name": "cross domain demo",
        },
        "nodes": [
            {
                "node_id": "A",
                "node_name": "A source",
                "skill": {
                    "skill_id": "piflow_engine.cn.piflow.engine.local.remote_source_stop.RemoteSourceStop",
                    "skill_name": "remote_source_stop",
                },
                "input_params": [
                    {
                        "param_name": "node_id",
                        "param_value": "10.0.0.1",
                        "value_mode": "manual",
                    },
                    {
                        "param_name": "remote_grpc_target",
                        "param_value": "10.0.0.1:50061",
                        "value_mode": "manual",
                    },
                ],
                "out_params": [{"param_name": "output", "param_type": "file"}],
            },
            {
                "node_id": "B",
                "node_name": "B source",
                "skill": {
                    "skill_id": "piflow_engine.cn.piflow.engine.local.remote_source_stop.RemoteSourceStop",
                    "skill_name": "remote_source_stop",
                },
                "input_params": [
                    {
                        "param_name": "node_id",
                        "param_value": "10.0.0.2",
                        "value_mode": "manual",
                    },
                    {
                        "param_name": "remote_grpc_target",
                        "param_value": "10.0.0.2:50061",
                        "value_mode": "manual",
                    },
                ],
                "out_params": [{"param_name": "output", "param_type": "file"}],
            },
        ],
        "edges": [],
        "bindings": [],
    }

    def resource_resolver(node: dict[str, object]):
        node_id = next(
            str(param.get("param_value"))
            for param in node.get("input_params", [])
            if param.get("param_name") == "node_id"
        )
        if node_id == "10.0.0.1":
            return type("R", (), {"node_id": node_id, "cpu_cores": 2.0, "memory_gb": 4.0, "free_disk_gb": 10.0})()
        return type("R", (), {"node_id": node_id, "cpu_cores": 8.0, "memory_gb": 16.0, "free_disk_gb": 100.0})()

    plan = schedule_frontend_dag(dag_definition, resource_resolver=resource_resolver)

    assert plan.execution_node_id == "10.0.0.2"
