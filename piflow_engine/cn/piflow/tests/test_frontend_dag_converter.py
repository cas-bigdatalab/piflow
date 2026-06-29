from __future__ import annotations

from cn.piflow.core.frontend_dag_converter import convert_frontend_dag_to_piflow


def test_convert_frontend_dag_to_piflow_uses_ids_for_paths() -> None:
    dag = {
        "task": {
            "task_id": "b3691c8a124d4c619a77904f7422465e",
            "task_name": "csv空行、空格清洗任务",
        },
        "edges": [
            {
                "from_node_id": "ignored-source",
                "to_node_id": "ignored-target",
            }
        ],
        "nodes": [
            {
                "node_id": "e1f6a960c5454e1b92d7e1bdb2a680e8",
                "node_name": "空行清洗节点",
                "skill": {
                    "skill_id": "42a28dca61f44455b789cde5b0b4eb21",
                    "version": "1.0.0",
                },
                "input_params": [
                    {
                        "param_name": "input",
                        "param_value": "workspace/temp/森林每木调查数据-blank-line-space.csv",
                        "value_mode": "manual",
                    },
                    {
                        "param_name": "output",
                        "param_value": "workspace/outputs/森林每木调查数据-blank-space.csv",
                        "value_mode": "manual",
                    },
                    {
                        "param_name": "skip_missing_value",
                        "value_mode": "manual",
                    },
                ],
            },
            {
                "node_id": "593a473d01ef4f5da0c93db24441a1cc",
                "node_name": "空格清洗节点",
                "skill": {
                    "skill_id": "40f751e3cec24c4f8d5d5b45a97a2ccb",
                    "version": "1.0.0",
                },
                "input_params": [
                    {
                        "binding_id": "c3bfd56347804535889f84300c437816",
                        "param_name": "input_path",
                        "value_mode": "reference",
                    },
                    {
                        "param_name": "output_path",
                        "param_value": "workspace/outputs/森林每木调查数据-clean.csv",
                        "value_mode": "manual",
                    },
                ],
            },
        ],
        "bindings": [
            {
                "binding_id": "c3bfd56347804535889f84300c437816",
                "from_node_id": "e1f6a960c5454e1b92d7e1bdb2a680e8",
                "to_node_id": "593a473d01ef4f5da0c93db24441a1cc",
                "from_param_name": "output",
                "to_param_name": "input_path",
            }
        ],
    }

    piflow_json = convert_frontend_dag_to_piflow(dag)
    print(piflow_json)
    assert piflow_json == {
        "flow": {
            "uuid": "b3691c8a124d4c619a77904f7422465e",
            "name": "csv空行、空格清洗任务",
            "runMode": "RUN",
            "stops": [
                {
                    "uuid": "e1f6a960c5454e1b92d7e1bdb2a680e8",
                    "name": "空行清洗节点",
                    "bundle": "42a28dca61f44455b789cde5b0b4eb21",
                    "properties": {
                        "input": "workspace/temp/森林每木调查数据-blank-line-space.csv",
                        "output": "workspace/outputs/森林每木调查数据-blank-space.csv",
                    },
                },
                {
                    "uuid": "593a473d01ef4f5da0c93db24441a1cc",
                    "name": "空格清洗节点",
                    "bundle": "40f751e3cec24c4f8d5d5b45a97a2ccb",
                    "properties": {
                        "output_path": "workspace/outputs/森林每木调查数据-clean.csv",
                    },
                },
            ],
            "paths": [
                {
                    "from": "e1f6a960c5454e1b92d7e1bdb2a680e8",
                    "to": "593a473d01ef4f5da0c93db24441a1cc",
                    "outport": "output",
                    "inport": "input_path",
                }
            ],
        }
    }
