from pathlib import Path
from types import SimpleNamespace
import inspect

from services import dag_panel_service
from runtime import skill_manage
from runtime.skills_compat import install_deepagents_skills_refresh_compat
from tools.excutor import excutor_utils


def test_get_all_skills_list_includes_generated_skills(tmp_path, monkeypatch):
    workspace_root = tmp_path / "workspace"
    skills_dir = workspace_root / "skills"
    generated_dir = skills_dir / "generated"
    generated_skill_dir = generated_dir / "epub_metadata_cleaner"
    generated_skill_dir.mkdir(parents=True, exist_ok=True)
    (generated_skill_dir / "SKILL.md").write_text(
        "---\nname: epub_metadata_cleaner\ndescription: 清洗 EPUB 元数据\n---\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(skill_manage, "WORKSPACE_ROOT", workspace_root)
    monkeypatch.setattr(skill_manage, "SKILLS_DIR", skills_dir)
    monkeypatch.setattr(skill_manage, "GENERATED_SKILLS_DIR", generated_dir)

    results = skill_manage.get_all_skills_list()

    assert any(item["name"] == "epub_metadata_cleaner" for item in results)


def test_skills_refresh_compat_forces_reload_each_request():
    import deepagents.middleware.skills as skills_module

    captured = {}
    original_before = skills_module.SkillsMiddleware.before_agent
    original_abefore = skills_module.SkillsMiddleware.abefore_agent

    def fake_original(self, state, runtime, config):  # noqa: ANN001
        captured["has_key"] = "skills_metadata" in state
        return {"skills_metadata": [{"name": "new-skill"}]}

    async def fake_aoriginal(self, state, runtime, config):  # noqa: ANN001
        captured["ah as_key"] = "skills_metadata" in state
        return {"skills_metadata": [{"name": "new-skill"}]}

    skills_module.SkillsMiddleware.before_agent = fake_original
    skills_module.SkillsMiddleware.abefore_agent = fake_aoriginal
    try:
        install_deepagents_skills_refresh_compat()
        wrapper = skills_module.SkillsMiddleware.before_agent
        middleware = SimpleNamespace()
        state = {"skills_metadata": [{"name": "old-skill"}]}
        result = wrapper(middleware, state, SimpleNamespace(), {})
    finally:
        skills_module.SkillsMiddleware.before_agent = original_before
        skills_module.SkillsMiddleware.abefore_agent = original_abefore

    assert captured["has_key"] is False
    assert result == {"skills_metadata": [{"name": "new-skill"}]}


def test_resolve_dag_definition_skills_falls_back_to_generated_skill_json(tmp_path, monkeypatch):
    workspace_root = tmp_path / "workspace"
    generated_skill_dir = workspace_root / "skills" / "generated" / "docx_to_markdown"
    generated_skill_dir.mkdir(parents=True, exist_ok=True)
    skill_json = generated_skill_dir / "skill.json"
    skill_json.write_text('{"name":"docx_to_markdown"}', encoding="utf-8")

    monkeypatch.setattr(excutor_utils, "resolve_workspace_root", lambda: workspace_root)
    monkeypatch.setattr(
        excutor_utils,
        "get_dag_skill",
        lambda skill_id: SimpleNamespace(skill_path="skills/docx_to_markdown"),
    )

    dag_definition = {
        "nodes": [
            {
                "node_id": "node-1",
                "skill": {
                    "skill_id": "legacy-docx-skill-id",
                    "version": "1.0.0",
                },
            }
        ]
    }

    resolved = excutor_utils.resolve_dag_definition_skills(dag_definition)

    assert resolved["nodes"][0]["skill"]["skill_id"] == str(skill_json.resolve())


def test_resolve_dag_definition_skills_uses_skill_name_when_skill_id_is_stale(tmp_path, monkeypatch):
    workspace_root = tmp_path / "workspace"
    generated_skill_dir = workspace_root / "skills" / "generated" / "epub_metadata_cleaner"
    generated_skill_dir.mkdir(parents=True, exist_ok=True)
    skill_json = generated_skill_dir / "skill.json"
    skill_json.write_text('{"name":"epub_metadata_cleaner"}', encoding="utf-8")

    monkeypatch.setattr(excutor_utils, "resolve_workspace_root", lambda: workspace_root)
    monkeypatch.setattr(excutor_utils, "get_dag_skill", lambda skill_id: None)

    dag_definition = {
        "nodes": [
            {
                "node_id": "node-1",
                "skill": {
                    "skill_id": "stale-generated-skill-id",
                    "skill_name": "epub_metadata_cleaner",
                    "version": "1.0.0",
                },
            }
        ]
    }

    resolved = excutor_utils.resolve_dag_definition_skills(dag_definition)

    assert resolved["nodes"][0]["skill"]["skill_id"] == str(skill_json.resolve())
    assert resolved["nodes"][0]["skill"]["skill_name"] == "epub_metadata_cleaner"


def test_register_skill_from_disk_preserves_single_level_param_shape(tmp_path, monkeypatch):
    workspace_root = tmp_path / "workspace"
    skill_dir = workspace_root / "skills" / "generated" / "demo_skill"
    scripts_dir = skill_dir / "scripts"
    scripts_dir.mkdir(parents=True, exist_ok=True)
    (scripts_dir / "run_demo_skill.py").write_text("print('ok')", encoding="utf-8")
    (skill_dir / "SKILL.md").write_text(
        (
            "---\n"
            "name: demo_skill\n"
            "name_zh: 演示技能\n"
            "description: 演示\n"
            "tag: 转换\n"
            "input_params:\n"
            "  - name: input_path\n"
            "    type: string\n"
            "    required: true\n"
            "output_params:\n"
            "  - name: output_path\n"
            "    type: string\n"
            "---\n"
        ),
        encoding="utf-8",
    )
    skill_json = skill_dir / "skill.json"
    skill_json.write_text('{"name":"demo_skill"}', encoding="utf-8")

    captured = {}

    def fake_insert_dag_skill(**kwargs):
        captured.update(kwargs)

    monkeypatch.setattr(excutor_utils, "resolve_workspace_root", lambda: workspace_root)

    import sys
    fake_skill_manage = SimpleNamespace(
        _parse_dag_skill_frontmatter=skill_manage._parse_dag_skill_frontmatter,
        insert_dag_skill=fake_insert_dag_skill,
    )
    monkeypatch.setitem(sys.modules, "runtime.skill_manage", fake_skill_manage)

    excutor_utils._register_skill_from_disk(workspace_root, "demo_skill", skill_json)

    assert captured["input_params"] == {
        "params": [
            {
                "name": "input_path",
                "type": "string",
                "description": "",
                "required": True,
            }
        ]
    }
    assert captured["output_params"] == {
        "params": [
            {
                "name": "output_path",
                "type": "string",
                "description": "",
            }
        ]
    }


def test_resolve_dag_definition_skills_promotes_top_level_skill_name(tmp_path, monkeypatch):
    workspace_root = tmp_path / "workspace"
    skill_dir = workspace_root / "skills" / "generated" / "docx_to_markdown"
    skill_dir.mkdir(parents=True, exist_ok=True)
    skill_json = skill_dir / "skill.json"
    skill_json.write_text('{"name":"docx_to_markdown"}', encoding="utf-8")

    monkeypatch.setattr(excutor_utils, "resolve_workspace_root", lambda: workspace_root)
    monkeypatch.setattr(excutor_utils, "get_dag_skill", lambda skill_id: None)

    dag_definition = {
        "nodes": [
            {
                "node_id": "node-1",
                "node_name": "DOCX转Markdown",
                "skill_name": "docx_to_markdown",
            }
        ]
    }

    resolved = excutor_utils.resolve_dag_definition_skills(dag_definition)

    assert resolved["nodes"][0]["skill"]["skill_id"] == str(skill_json.resolve())
    assert resolved["nodes"][0]["skill"]["skill_name"] == "docx_to_markdown"


def test_resolve_dag_definition_skills_falls_back_to_nested_workspace_generated_skill(tmp_path, monkeypatch):
    workspace_root = tmp_path / "workspace"
    nested_skill_dir = (
        workspace_root
        / "workspace"
        / "skills"
        / "generated"
        / "sofa_validate"
    )
    nested_skill_dir.mkdir(parents=True, exist_ok=True)
    skill_json = nested_skill_dir / "skill.json"
    skill_json.write_text('{"name":"sofa_validate"}', encoding="utf-8")

    monkeypatch.setattr(excutor_utils, "resolve_workspace_root", lambda: workspace_root)
    monkeypatch.setattr(excutor_utils, "get_dag_skill", lambda skill_id: None)

    dag_definition = {
        "nodes": [
            {
                "node_id": "node-1",
                "node_name": "SOFA 校验",
                "skill_name": "sofa_validate",
            }
        ]
    }

    resolved = excutor_utils.resolve_dag_definition_skills(dag_definition)

    assert resolved["nodes"][0]["skill"]["skill_id"] == str(skill_json.resolve())
    assert resolved["nodes"][0]["skill"]["skill_name"] == "sofa_validate"


def test_resolve_dag_definition_skills_fills_builtin_stop_bundle_without_skill_block(monkeypatch):
    monkeypatch.setattr(excutor_utils, "resolve_workspace_root", lambda: Path("/tmp/workspace"))
    monkeypatch.setattr(excutor_utils, "get_dag_skill", lambda skill_id: None)

    dag_definition = {
        "nodes": [
            {
                "node_id": "node-1",
                "node_name": "输入文件节点1",
                "skill_name": "source_stop",
            },
            {
                "node_id": "node-2",
                "node_name": "输出文件节点1",
                "skill_name": "sink_stop",
            },
        ]
    }

    resolved = excutor_utils.resolve_dag_definition_skills(dag_definition)

    assert (
        resolved["nodes"][0]["skill"]["skill_id"]
        == "cn.piflow.engine.local.source_file_stop.SourceFileStop"
    )
    assert resolved["nodes"][1]["skill"]["skill_id"] == "cn.piflow.engine.local.file_save_stop.FileSaveStop"


def test_resolve_dag_definition_skills_preserves_builtin_stop_bundle_when_db_points_to_system_node(
    tmp_path, monkeypatch
):
    workspace_root = tmp_path / "workspace"
    source_dir = workspace_root / "dag_system_node" / "source_stop"
    sink_dir = workspace_root / "dag_system_node" / "sink_stop"
    source_dir.mkdir(parents=True, exist_ok=True)
    sink_dir.mkdir(parents=True, exist_ok=True)
    (source_dir / "skill.json").write_text('{"name":"source_stop"}', encoding="utf-8")
    (sink_dir / "skill.json").write_text('{"name":"sink_stop"}', encoding="utf-8")

    monkeypatch.setattr(excutor_utils, "resolve_workspace_root", lambda: workspace_root)

    def fake_get_dag_skill(skill_id):
        mapping = {
            "cn.piflow.engine.local.source_file_stop.SourceFileStop": "dag_system_node/source_stop",
            "cn.piflow.engine.local.file_save_stop.FileSaveStop": "dag_system_node/sink_stop",
        }
        skill_path = mapping.get(skill_id)
        if skill_path is None:
            return None
        return SimpleNamespace(skill_path=skill_path)

    monkeypatch.setattr(excutor_utils, "get_dag_skill", fake_get_dag_skill)

    dag_definition = {
        "nodes": [
            {
                "node_id": "node-1",
                "node_name": "输入文件节点 1",
                "skill": {
                    "skill_id": "cn.piflow.engine.local.source_file_stop.SourceFileStop",
                    "skill_name": "source_stop",
                    "version": "1.0.0",
                },
            },
            {
                "node_id": "node-2",
                "node_name": "输出文件节点 1",
                "skill": {
                    "skill_id": "cn.piflow.engine.local.file_save_stop.FileSaveStop",
                    "skill_name": "sink_stop",
                    "version": "1.0.0",
                },
            },
        ]
    }

    resolved = excutor_utils.resolve_dag_definition_skills(dag_definition)

    assert (
        resolved["nodes"][0]["skill"]["skill_id"]
        == "cn.piflow.engine.local.source_file_stop.SourceFileStop"
    )
    assert resolved["nodes"][1]["skill"]["skill_id"] == "cn.piflow.engine.local.file_save_stop.FileSaveStop"


def test_insert_dag_skill_upsert_preserves_existing_skill_id():
    source = inspect.getsource(skill_manage.insert_dag_skill)

    assert "ON CONFLICT (skill_name, version)" in source
    assert "skill_id = EXCLUDED.skill_id" not in source


def test_save_dag_panel_normalizes_definition_before_persist(monkeypatch):
    captured = {}

    class DummyConn:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def close(self):
            return None

    monkeypatch.setattr(dag_panel_service, "get_connection", lambda: DummyConn())
    monkeypatch.setattr(dag_panel_service, "create_or_update_task", lambda conn, task, create_user_id: "task-1")
    monkeypatch.setattr(dag_panel_service, "get_next_revision", lambda conn, task_id, create_user_id: 1)
    monkeypatch.setattr(dag_panel_service, "disable_current_definition", lambda conn, task_id, create_user_id: None)

    def fake_insert(conn, task_id, create_user_id, revision, definition_json):
        captured["definition_json"] = definition_json
        return "definition-1"

    monkeypatch.setattr(dag_panel_service, "insert_dag_definition", fake_insert)
    monkeypatch.setattr(
        dag_panel_service,
        "resolve_dag_definition_skills",
        lambda definition_json: {
            **definition_json,
            "nodes": [
                {
                    **definition_json["nodes"][0],
                    "skill": {
                        "skill_id": "/resolved/workspace/skills/generated/sofa_to_csv/skill.json",
                        "skill_name": "sofa_to_csv",
                    },
                }
            ],
        },
    )

    raw_definition = {
        "dsl_version": "1.0",
        "task": {"dag_task_id": "", "dag_task_name": "SOFA 转 CSV", "description": "", "message_id": ""},
        "nodes": [
            {
                "node_id": "node-1",
                "node_name": "SOFA导出CSV",
                "skill_name": "sofa_to_csv",
                "skill": {"skill_id": "", "version": "1.0"},
            }
        ],
        "edges": [],
        "bindings": [],
    }

    result = dag_panel_service.save_dag_panel(raw_definition, "user-1")

    assert result == {"task_id": "task-1", "definition_id": "definition-1", "revision": 1}
    assert captured["definition_json"]["nodes"][0]["skill"]["skill_id"] == "/resolved/workspace/skills/generated/sofa_to_csv/skill.json"
    assert captured["definition_json"]["nodes"][0]["skill"]["skill_name"] == "sofa_to_csv"
