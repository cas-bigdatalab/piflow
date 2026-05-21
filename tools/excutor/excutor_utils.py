from pathlib import Path

from infra.config_loader import get_settings, resolve_workspace_root
from runtime.dag_manager import get_dag_skill

example_json = """{"task": {"task_id": "b3691c8a124d4c619a77904f7422465e", "task_name": "csv空行、空格清洗任务", "message_id": "test_message_id_123", "description": "对csv文件的空行和字段值前后空格进行清洗"}, "edges": [{"edge_id": "e666d658c2614f5085ce112707647965", "to_node_id": "593a473d01ef4f5da0c93db24441a1cc", "from_node_id": "e1f6a960c5454e1b92d7e1bdb2a680e8"}], "nodes": [{"skill": {"version": "1.0.0", "skill_id": "42a28dca61f44455b789cde5b0b4eb21"}, "node_id": "e1f6a960c5454e1b92d7e1bdb2a680e8", "position": {"x": 100.0, "y": 200.0}, "node_name": "空行清洗节点", "node_type": "default", "input_params": [{"param_name": "input", "param_type": "String", "value_mode": "manual", "param_value": "workspace/temp/森林每木调查数据-blank-line-space.csv", "value_source": "local_file"}, {"param_name": "output", "param_type": "String", "value_mode": "manual", "param_value": "workspace/outputs/森林每木调查数据-blank-space.csv", "value_source": "local_file"}]}, {"skill": {"version": "1.0.0", "skill_id": "40f751e3cec24c4f8d5d5b45a97a2ccb"}, "node_id": "593a473d01ef4f5da0c93db24441a1cc", "position": {"x": 400.0, "y": 200.0}, "node_name": "空格清洗节点", "node_type": "default", "input_params": [{"binding_id": "c3bfd56347804535889f84300c437816", "param_name": "input_path", "param_type": "String", "value_mode": "reference"}, {"param_name": "output_path", "param_type": "String", "value_mode": "manual", "param_value": "workspace/outputs/森林每木调查数据-clean.csv", "value_source": "local_file"}]}], "bindings": [{"binding_id": "c3bfd56347804535889f84300c437816", "to_node_id": "593a473d01ef4f5da0c93db24441a1cc", "from_node_id": "e1f6a960c5454e1b92d7e1bdb2a680e8", "to_param_name": "input_path", "from_param_name": "output"}], "dsl_version": "1.0"}"""

settings = get_settings()

workspace_root = settings.workspace.root


def resolve_dag_definition_skills(dag_definition: dict) -> dict:
    _workspace_root = resolve_workspace_root()

    def _resolve_node_skill(node: dict) -> dict:
        skill = node.get("skill")
        if not skill:
            return node

        skill_id = skill.get("skill_id")
        if not skill_id:
            return node

        dag_skill = get_dag_skill(skill_id)
        if not dag_skill or not dag_skill.skill_path:
            return node

        skill_json_path = str(
            (_workspace_root / dag_skill.skill_path / "skill.json").resolve()
        )

        updated_skill = {**skill, "skill_id": skill_json_path}
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

