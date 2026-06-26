from pathlib import Path

from infra.config_loader import get_settings, resolve_workspace_root
from runtime.dag_manager import get_dag_skill


def _register_skill_from_disk(workspace_root: Path, skill_name: str, skill_path: Path) -> None:
    """将磁盘上的 skill 注册到 dag_skills 表（如果尚未注册）。"""
    try:
        from runtime.skill_manage import _parse_dag_skill_frontmatter, insert_dag_skill
    except ImportError:
        return

    skill_dir = skill_path.parent
    info = _parse_dag_skill_frontmatter(skill_dir)
    if info is None:
        return

    rel_path = skill_dir.relative_to(workspace_root).as_posix()
    file_path = ""
    for script_candidate in (
        skill_dir / "scripts",
    ):
        if script_candidate.is_dir():
            scripts = sorted(script_candidate.iterdir())
            if scripts:
                file_path = str(scripts[0])
            break

    input_params = info.get("input_params", [])
    output_params = info.get("output_params", [])

    insert_dag_skill(
        skill_name=info["name"],
        name_zh=info.get("name_zh", ""),
        description=info["description"],
        skill_path=rel_path,
        file_path=file_path,
        input_params={"params": input_params},
        output_params={"params": output_params},
        skill_type=info.get("tag", ""),
        language="Python",
        command="",
        icon_path=f"/storage/{rel_path}/{skill_name}.png",
        version=info.get("version", "1.0.0"),
    )

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


def _candidate_workspace_roots(workspace_root: Path) -> list[Path]:
    roots: list[Path] = []
    for candidate in (workspace_root, workspace_root / "workspace"):
        resolved = candidate.resolve()
        if resolved not in roots:
            roots.append(resolved)
    return roots


def _resolve_skill_json_path_by_name(workspace_root: Path, skill_name: str) -> Path | None:
    normalized_name = str(skill_name or "").strip()
    if not normalized_name:
        return None

    for root in _candidate_workspace_roots(workspace_root):
        candidates = [
            root / "skills" / normalized_name / "skill.json",
            root / "skills" / "generated" / normalized_name / "skill.json",
            root / "dag_system_node" / normalized_name / "skill.json",
        ]
        for candidate in candidates:
            resolved = candidate.resolve()
            if resolved.exists():
                return resolved

    return None


def _resolve_skill_json_path_by_name_zh(workspace_root: Path, name_zh: str) -> Path | None:
    """按 name_zh（中文名）在所有技能目录中查找 skill.json。"""
    normalized = str(name_zh or "").strip()
    if not normalized:
        return None

    from runtime.skill_manage import _parse_dag_skill_frontmatter

    for root in _candidate_workspace_roots(workspace_root):
        for base_dir in [
            root / "skills",
            root / "skills" / "generated",
            root / "dag_system_node",
        ]:
            if not base_dir.exists():
                continue
            for skill_dir in base_dir.iterdir():
                if not skill_dir.is_dir():
                    continue
                info = _parse_dag_skill_frontmatter(skill_dir)
                if info is None:
                    continue
                if info.get("name_zh") == normalized:
                    skill_json = skill_dir / "skill.json"
                    if skill_json.exists():
                        return skill_json.resolve()

    return None


def _resolve_skill_json_path(workspace_root: Path, skill_path: str) -> Path:
    skill_name = Path(skill_path).name

    for root in _candidate_workspace_roots(workspace_root):
        primary = (root / skill_path / "skill.json").resolve()
        if primary.exists():
            return primary

        generated = (root / "skills" / "generated" / skill_name / "skill.json").resolve()
        if generated.exists():
            return generated

    return (workspace_root / skill_path / "skill.json").resolve()


def resolve_dag_definition_skills(dag_definition: dict) -> dict:
    _workspace_root = resolve_workspace_root()
    builtin_skill_ids = {
        "source_stop": "cn.piflow.engine.local.source_file_stop.SourceFileStop",
        "sink_stop": "cn.piflow.engine.local.file_save_stop.FileSaveStop",
    }
    builtin_skill_id_values = set(builtin_skill_ids.values())

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

        # PiFlow 内置 stop 必须保留 class bundle，不能被 dag_system_node/skill.json 覆盖。
        if skill_id in builtin_skill_id_values:
            updated_skill = {
                **skill,
                "skill_id": skill_id,
            }
            if skill_name:
                updated_skill["skill_name"] = skill_name
            return {**node, "skill": updated_skill}

        skill_json_path: str | None = None

        # 路径1: 通过 skill_id 查 dag_skills 表
        if skill_id:
            dag_skill = get_dag_skill(skill_id)
            if dag_skill and dag_skill.skill_path:
                skill_json_path = str(_resolve_skill_json_path(_workspace_root, dag_skill.skill_path))

        # 路径2: 按 skill_name 在文件系统查找（覆盖 DB 查不到的情况）
        if not skill_json_path and skill_name:
            resolved_by_name = _resolve_skill_json_path_by_name(_workspace_root, skill_name)
            if resolved_by_name is None:
                resolved_by_name = _resolve_skill_json_path_by_name_zh(_workspace_root, skill_name)
            if resolved_by_name is not None:
                skill_json_path = str(resolved_by_name)
                skill_name = Path(resolved_by_name).parent.name

        # 路径3: 按 node_name 兜底（覆盖前端未保留 skill_name 的情况）
        if not skill_json_path and not skill_name and node_name:
            resolved_by_node = _resolve_skill_json_path_by_name(_workspace_root, node_name)
            if resolved_by_node is None:
                resolved_by_node = _resolve_skill_json_path_by_name_zh(_workspace_root, node_name)
            if resolved_by_node is not None:
                skill_json_path = str(resolved_by_node)
                skill_name = Path(resolved_by_node).parent.name

        # 路径4: 用 skill_name 或 node_name 扫描所有技能目录（兜底中的兜底）
        if not skill_json_path:
            search_names = [n for n in [skill_name, node_name] if n]
            for search_name in search_names:
                resolved = _resolve_skill_json_path_by_name(_workspace_root, search_name)
                if resolved is None:
                    resolved = _resolve_skill_json_path_by_name_zh(_workspace_root, search_name)
                if resolved is not None:
                    skill_json_path = str(resolved)
                    skill_name = Path(resolved).parent.name
                    break

        # 文件系统解析成功但 DB 中无记录 → 自动注册
        if skill_json_path and skill_name:
            resolved_path = Path(skill_json_path)
            if resolved_path.exists():
                _register_skill_from_disk(_workspace_root, skill_name, resolved_path)

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

