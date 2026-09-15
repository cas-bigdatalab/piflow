import json
import sys
import uuid
from collections.abc import Callable
from typing import Any, Optional, TypedDict


SkillFetcher = Callable[[str], dict[str, Any]]


class JsonConvertToolInput(TypedDict):
    definition_json: dict[str, Any]


class JsonConvertToolOutput(TypedDict):
    definition_json: dict[str, Any]


def _validate_definition_json(definition_json: dict[str, Any]) -> None:
    if not isinstance(definition_json, dict):
        raise ValueError("definition_json must be a dict")
    if not isinstance(definition_json.get("task"), dict):
        raise ValueError("definition_json.task must be a dict")
    if not isinstance(definition_json.get("nodes"), list):
        raise ValueError("definition_json.nodes must be a list")


def _default_fetch_skill(skill_name: str) -> dict[str, Any]:
    from services.dag_panel_service import get_dag_skills_by_condition

    result = get_dag_skills_by_condition(keyword=skill_name)
    for group in result.get("data", []):
        for skill in group.get("DagSkillInfoList", []):
            if hasattr(skill, "skill_name") and skill.skill_name == skill_name:
                return {
                    "skill_id": skill.skill_id,
                    "version": skill.version,
                    "name_zh": getattr(skill, "name_zh", None),
                    "icon_path": getattr(skill, "icon_path", "") or "",
                    "input_params": skill.input_params.get("params", []),
                    "output_params": skill.output_params.get("params", []),
                }
            if isinstance(skill, dict) and skill.get("skill_name") == skill_name:
                return skill
    raise ValueError(f"skill not found: {skill_name}")


def _build_source_stop(node: dict[str, Any], node_id: str) -> dict[str, Any]:
    return {
        "node_id": node_id,
        "node_name": node["node_name"],
        "node_type": "default",
        "icon_path": "",
        "skill": {
            "skill_id": "cn.piflow.piflow_engine.local.source_file_stop.SourceFileStop",
            "version": "1.0",
        },
        "input_params": [
            {
                "param_name": "file_path",
                "param_value": node["params"].get("file_path"),
            }
        ],
        "out_params": [
            {
                "param_name": "output",
            }
        ],
    }


def _build_sink_stop(node: dict[str, Any], node_id: str) -> dict[str, Any]:
    return {
        "node_id": node_id,
        "node_name": node["node_name"],
        "node_type": "default",
        "icon_path": "",
        "skill": {
            "skill_id": "cn.piflow.piflow_engine.local.file_save_stop.FileSaveStop",
            "version": "1.0",
        },
        "input_params": [
            {
                "param_name": "input",
                "param_value": node["params"].get("input"),
            },
            {
                "param_name": "path",
                "param_value": node["params"].get("path"),
            },
            {
                "param_name": "overwrite",
                "param_value": node["params"].get("overwrite"),
            },
        ],
        "out_params": [],
    }


def _build_normal_node(
    node: dict[str, Any],
    node_id: str,
    fetch_skill: SkillFetcher,
) -> dict[str, Any]:
    skill_meta = fetch_skill(node["skill_name"])
    params = node.get("params", {})

    output_names = {
        item.get("name")
        for item in skill_meta.get("output_params", [])
        if item.get("name")
    }

    input_params = []
    for item in skill_meta.get("input_params", []):
        param_name = item.get("name")
        if not param_name or param_name in output_names:
            continue
        if param_name not in params:
            continue
        input_params.append(
            {
                "param_name": param_name,
                "param_value": params.get(param_name),
            }
        )

    out_params = []
    for item in skill_meta.get("output_params", []):
        param_name = item.get("name")
        if not param_name:
            continue
        out_param = {
            "param_name": param_name,
        }
        param_type = item.get("type")
        if param_type:
            out_param["param_type"] = param_type
        out_params.append(out_param)

    return {
        "node_id": node_id,
        "node_name": node["node_name"],
        "node_type": "default",
        "icon_path": skill_meta.get("icon_path", ""),
        "skill": {
            "skill_id": skill_meta["skill_id"],
            "version": skill_meta.get("version", "1.0.0"),
        },
        "input_params": input_params,
        "out_params": out_params,
    }


def convert_json_a_to_b(
    json_a: dict[str, Any],
    *,
    fetch_skill: Optional[SkillFetcher] = None,
) -> dict[str, Any]:
    fetch_skill = fetch_skill or _default_fetch_skill
    node_name_to_id: dict[str, str] = {}
    converted_nodes: list[dict[str, Any]] = []

    for node in json_a.get("nodes", []):
        node_id = str(uuid.uuid4())
        node_name_to_id[node["node_name"]] = node_id

        if node["skill_name"] == "source_stop":
            converted_nodes.append(_build_source_stop(node, node_id))
        elif node["skill_name"] == "sink_stop":
            converted_nodes.append(_build_sink_stop(node, node_id))
        else:
            converted_nodes.append(_build_normal_node(node, node_id, fetch_skill))

    bindings = []
    for node in json_a.get("nodes", []):
        to_node_id = node_name_to_id[node["node_name"]]
        for input_key, input_value in node.get("params", {}).items():
            if not isinstance(input_value, dict):
                continue
            if "source_node" not in input_value or "source_param" not in input_value:
                continue
            bindings.append(
                {
                    "binding_id": str(uuid.uuid4()),
                    "to_node_id": to_node_id,
                    "from_node_id": node_name_to_id[input_value["source_node"]],
                    "to_param_name": input_key,
                    "from_param_name": input_value["source_param"],
                }
            )

    return {
        "dsl_version": "1.0",
        "task": {
            "dag_task_id": "",
            "dag_task_name": json_a["task"]["name"],
            "description": json_a["task"]["description"],
            "message_id": "",
        },
        "nodes": converted_nodes,
        "edges": [],
        "bindings": bindings,
    }


def convert_json_tool(
    definition_json: dict[str, Any],
    *,
    fetch_skill: Optional[SkillFetcher] = None,
) -> JsonConvertToolOutput:
    """
    Service-facing entrypoint.

    入参:
        definition_json: 简化 DAG JSON，格式为 {"task": {...}, "nodes": [...]}。

    返回值:
        {"definition_json": <转换后的 DAG JSON>}。
    """
    _validate_definition_json(definition_json)
    converted = convert_json_a_to_b(
        definition_json,
        fetch_skill=fetch_skill,
    )
    return {"definition_json": converted}


def main() -> None:
    json_a = json.load(sys.stdin)
    json_b = convert_json_a_to_b(json_a)
    json.dump(json_b, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
