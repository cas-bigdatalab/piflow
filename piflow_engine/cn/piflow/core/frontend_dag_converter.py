from __future__ import annotations

from typing import Any


def convert_frontend_dag_to_piflow(dag: dict[str, Any]) -> dict[str, Any]:
    """Convert frontend DAG JSON into standard PiFlow JSON."""
    task = dict(dag.get("task", {}))

    return {
        "flow": {
            "uuid": str(task.get("dag_task_id", "")),
            "name": str(task.get("dag_task_name", "")),
            "runMode": "RUN",
            "stops": [_convert_node_to_stop(node) for node in dag.get("nodes", [])],
            "paths": [
                _convert_binding_to_path(binding)
                for binding in dag.get("bindings", [])
            ],
        }
    }


def _convert_node_to_stop(node: dict[str, Any]) -> dict[str, Any]:
    skill = dict(node.get("skill", {}))

    return {
        "uuid": str(node.get("node_id", "")),
        "name": str(node.get("node_name", "")),
        "bundle": str(skill.get("skill_id", "")),
        "properties": _convert_input_params_to_properties(
            node.get("input_params", []),
            node.get("out_params", []),
        ),
    }


def _convert_input_params_to_properties(
    input_params: list[dict[str, Any]],
    out_params: list[dict[str, Any]],
) -> dict[str, Any]:
    output_param_names = {
        str(param.get("param_name"))
        for param in out_params
        if param.get("param_name")
    }
    properties: dict[str, Any] = {}
    for param in input_params:
        if param.get("value_mode") == "reference":
            continue
        if "param_name" not in param or "param_value" not in param:
            continue
        param_name = str(param["param_name"])
        if param_name in output_param_names:
            continue
        properties[param_name] = param["param_value"]
    return properties


def _convert_binding_to_path(binding: dict[str, Any]) -> dict[str, str]:
    return {
        "from": str(binding.get("from_node_id", "")),
        "to": str(binding.get("to_node_id", "")),
        "outport": str(binding.get("from_param_name", "")),
        "inport": str(binding.get("to_param_name", "")),
    }


frontend_dag_to_piflow = convert_frontend_dag_to_piflow
