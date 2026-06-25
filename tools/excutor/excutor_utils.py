from pathlib import Path

from infra.config_loader import get_settings, resolve_workspace_root
from runtime.dag_manager import get_dag_skill

example_json = """{
    "task": {
        "dag_task_id": "47b35de7a1c843c3a4d89961948172fc",
        "dag_task_name": "科研数据清洗与排序"
    },
    "edges": [
        {
            "edge_id": "edge-node-1-node-2",
            "to_node_id": "node-2",
            "from_node_id": "node-1"
        },
        {
            "edge_id": "edge-node-2-node-3",
            "to_node_id": "node-3",
            "from_node_id": "node-2"
        }
    ],
    "nodes": [
        {
            "skill": {
                "version": "1.0",
                "skill_id": "b8855438d57442c98b6d9d1a28257e1e"
            },
            "node_id": "node-1",
            "position": {
                "x": 50,
                "y": 50
            },
            "icon_path": "/storage/skills/DC1_Blank_Line_Clean.png",
            "node_name": "DC1_空行清洗算子",
            "node_type": "default",
            "out_params": [
                {
                    "param_name": "output",
                    "param_type": "csv_file"
                }
            ],
            "input_params": [
                {
                    "binding_id": "",
                    "param_name": "input",
                    "param_type": "string",
                    "value_mode": "manual",
                    "param_value": "/temp/森林每木调查数据-blank-line-space.csv",
                    "value_source": "default"
                },
                {
                    "binding_id": "",
                    "param_name": "output",
                    "param_type": "string",
                    "value_mode": "manual",
                    "param_value": "/workspace/artifacts/no_blank_lines.csv",
                    "value_source": "default"
                }
            ]
        },
        {
            "skill": {
                "version": "1.0",
                "skill_id": "67a4fe930be84d2992fd426dbc9914e6"
            },
            "node_id": "node-2",
            "position": {
                "x": 395,
                "y": 50
            },
            "icon_path": "/storage/skills/DC2_SpaceCleaning.png",
            "node_name": "DC2_字符串空格清理算子",
            "node_type": "default",
            "out_params": [
                {
                    "param_name": "output_path",
                    "param_type": "csv_file"
                }
            ],
            "input_params": [
                {
                    "binding_id": "",
                    "param_name": "input_path",
                    "param_type": "string",
                    "value_mode": "manual",
                    "param_value": "",
                    "value_source": "default"
                },
                {
                    "binding_id": "",
                    "param_name": "output_path",
                    "param_type": "string",
                    "value_mode": "manual",
                    "param_value": "",
                    "value_source": "default"
                }
            ]
        },
        {
            "skill": {
                "version": "1.0",
                "skill_id": "16165c4f75e74a9c88206317258c1029"
            },
            "node_id": "node-3",
            "position": {
                "x": 740,
                "y": 50
            },
            "icon_path": "/storage/skills/Pi_DataSorting.png",
            "node_name": "Pi_数据排序算子",
            "node_type": "default",
            "out_params": [
                {
                    "param_name": "output_path",
                    "param_type": "csv_file"
                }
            ],
            "input_params": [
                {
                    "binding_id": "",
                    "param_name": "input_path",
                    "param_type": "string",
                    "value_mode": "manual",
                    "param_value": "",
                    "value_source": "default"
                },
                {
                    "binding_id": "",
                    "param_name": "output_path",
                    "param_type": "string",
                    "value_mode": "manual",
                    "param_value": "",
                    "value_source": "default"
                },
                {
                    "binding_id": "",
                    "param_name": "id_field_name",
                    "param_type": "string",
                    "value_mode": "manual",
                    "param_value": "",
                    "value_source": "default"
                },
                {
                    "binding_id": "",
                    "param_name": "sort_order",
                    "param_type": "string",
                    "value_mode": "manual",
                    "param_value": "",
                    "value_source": "default"
                }
            ]
        }
    ],
    "bindings": [

    ],
    "dsl_version": "1.0"
}"""
settings = get_settings()

workspace_root = settings.workspace.root


def _resolve_skill_json_path_by_name(workspace_root: Path, skill_name: str) -> Path | None:
    normalized_name = str(skill_name or "").strip()
    if not normalized_name:
        return None

    candidates = [
        workspace_root / "skills" / normalized_name / "skill.json",
        workspace_root / "skills" / "generated" / normalized_name / "skill.json",
        workspace_root / "dag_system_node" / normalized_name / "skill.json",
    ]

    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved.exists():
            return resolved

    return None


def _resolve_skill_json_path(workspace_root: Path, skill_path: str) -> Path:
    primary = (workspace_root / skill_path / "skill.json").resolve()
    if primary.exists():
        return primary

    skill_name = Path(skill_path).name
    generated = (workspace_root / "skills" / "generated" / skill_name / "skill.json").resolve()
    if generated.exists():
        return generated

    return primary


def resolve_dag_definition_skills(dag_definition: dict) -> dict:
    _workspace_root = resolve_workspace_root()
    builtin_skill_ids = {
        "source_stop": "cn.piflow.engine.local.source_file_stop.SourceFileStop",
        "sink_stop": "cn.piflow.engine.local.file_save_stop.FileSaveStop",
    }

    def _resolve_node_skill(node: dict) -> dict:
        raw_skill = node.get("skill")
        skill = dict(raw_skill) if isinstance(raw_skill, dict) else {}
        top_level_skill_name = str(node.get("skill_name", "")).strip()
        skill_name = str(skill.get("skill_name", "")).strip() or top_level_skill_name
        node_name = str(node.get("node_name", "")).strip()

        if not skill_name and node_name in builtin_skill_ids:
            skill_name = node_name

        skill_id = skill.get("skill_id")
        if not skill_id and skill_name in builtin_skill_ids:
            skill_id = builtin_skill_ids[skill_name]
        if not skill_id and isinstance(raw_skill, str) and raw_skill.strip():
            skill_id = raw_skill.strip()

        skill_json_path: str | None = None
        if skill_id:
            dag_skill = get_dag_skill(skill_id)
            if dag_skill and dag_skill.skill_path:
                skill_json_path = str(_resolve_skill_json_path(_workspace_root, dag_skill.skill_path))

        if not skill_json_path and skill_name:
            resolved_by_name = _resolve_skill_json_path_by_name(_workspace_root, skill_name)
            if resolved_by_name is not None:
                skill_json_path = str(resolved_by_name)

        resolved_skill_id = skill_json_path or skill_id or ""
        if not resolved_skill_id:
            return node

        updated_skill = {
            **skill,
            "skill_id": resolved_skill_id,
        }
        if skill_name:
            updated_skill["skill_name"] = skill_name
        return {**node, "skill": updated_skill}

    nodes = [_resolve_node_skill(n) for n in dag_definition.get("nodes", [])]
    return {**dag_definition, "nodes": nodes}


if __name__ == "__main__":
    import json
    from runtime.dag_manager import list_dag_skills

    skills_resp = list_dag_skills(page=1, page_size=2)
    skills = skills_resp.get("data", [])
    if not skills:
        print("dag_skills 表为空，请先执行 init_dag_skills_to_database()")
        exit(1)

    template = json.loads(example_json)
    for i, node in enumerate(template["nodes"]):
        if i < len(skills):
            node["skill"]["skill_id"] = skills[i].skill_id

    result = resolve_dag_definition_skills(template)
    print(json.dumps(result, ensure_ascii=False, indent=2))

