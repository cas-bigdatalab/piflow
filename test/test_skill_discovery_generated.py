from pathlib import Path
from types import SimpleNamespace
import inspect

from services import dag_panel_service
from runtime import skill_manage
from runtime.skills_compat import install_deepagents_skills_refresh_compat
from runtime import piflow_adapter


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


def test_update_generated_dag_skills_in_database_registers_single_generated_skill(tmp_path, monkeypatch):
    workspace_root = tmp_path / "workspace"
    skills_dir = workspace_root / "skills"
    generated_dir = skills_dir / "generated"
    skill_dir = generated_dir / "fasta_fna_validator"
    scripts_dir = skill_dir / "scripts"
    scripts_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(
        (
            "---\n"
            "name: fasta_fna_validator\n"
            "name_zh: FASTA/FNA序列校验工具\n"
            "description: FASTA/FNA 校验\n"
            "tag: 数据校验\n"
            "input_params:\n"
            "  - name: input_path\n"
            "    role: input_data\n"
            "    type: string\n"
            "    required: true\n"
            "    description: 输入文件路径\n"
            "output_params:\n"
            "  - name: report_path\n"
            "    role: output_data\n"
            "    type: json_file\n"
            "    description: 报告输出路径\n"
            "---\n"
            "\n"
            "```bash\n"
            "python scripts/run_fasta_fna_validator.py --input_path {input_path}\n"
            "```\n"
        ),
        encoding="utf-8",
    )
    (skill_dir / "skill.json").write_text('{"name":"fasta_fna_validator"}', encoding="utf-8")
    (scripts_dir / "run_fasta_fna_validator.py").write_text("print('ok')\n", encoding="utf-8")

    monkeypatch.setattr(skill_manage, "WORKSPACE_ROOT", workspace_root)
    monkeypatch.setattr(skill_manage, "SKILLS_DIR", skills_dir)
    monkeypatch.setattr(skill_manage, "GENERATED_SKILLS_DIR", generated_dir)
    monkeypatch.setattr(skill_manage, "DAG_SYSTEM_NODE_DIR", workspace_root / "dag_system_node")

    captured = {}

    def fake_insert_dag_skill(**kwargs):
        captured.update(kwargs)
        return {"id": 1, "skill_id": "generated-skill-id"}

    monkeypatch.setattr(skill_manage, "insert_dag_skill", fake_insert_dag_skill)

    result = skill_manage.update_generated_dag_skills_in_database(skill_dir=skill_dir)

    assert result["count"] == 1
    assert result["skills"][0]["skill_id"] == "generated-skill-id"
    assert captured["skill_name"] == "fasta_fna_validator"
    assert captured["skill_path"] == "skills/generated/fasta_fna_validator"
    assert captured["input_params"]["params"][0]["name"] == "input_path"
    assert captured["language"] == "Python"
    assert "run_fasta_fna_validator.py" in captured["command"]


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


def test_parse_dag_skill_frontmatter_preserves_roles_and_keeps_output_data_out_of_input_params(tmp_path, monkeypatch):
    workspace_root = tmp_path / "workspace"
    skills_dir = workspace_root / "skills"
    generated_dir = skills_dir / "generated"
    skill_dir = generated_dir / "ttf_to_otf_converter"
    skill_dir.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(skill_manage, "WORKSPACE_ROOT", workspace_root)
    monkeypatch.setattr(skill_manage, "SKILLS_DIR", skills_dir)
    monkeypatch.setattr(skill_manage, "GENERATED_SKILLS_DIR", generated_dir)

    (skill_dir / "SKILL.md").write_text(
        (
            "---\n"
            "name: ttf_to_otf_converter\n"
            "name_zh: TTF转OTF字体转换工具\n"
            "description: test skill\n"
            "tag: 业务\n"
            "input_params:\n"
            "  - name: input_path\n"
            "    type: string\n"
            "    role: input_data\n"
            "    required: true\n"
            "  - name: output_path\n"
            "    type: string\n"
            "    role: output_data\n"
            "    required: false\n"
            "output_params:\n"
            "  - name: output_path\n"
            "    type: string\n"
            "    role: output_data\n"
            "---\n"
        ),
        encoding="utf-8",
    )

    parsed = skill_manage._parse_dag_skill_frontmatter(skill_dir)

    assert parsed is not None
    assert parsed["input_params"] == {
        "params": [
            {
                "name": "input_path",
                "type": "string",
                "role": "input_data",
                "description": "",
                "required": True,
            }
        ]
    }
    assert parsed["output_params"] == {
        "params": [
            {
                "name": "output_path",
                "type": "string",
                "role": "output_data",
                "description": "",
            }
        ]
    }
def test_insert_dag_skill_upsert_preserves_existing_skill_id():
    source = inspect.getsource(skill_manage.insert_dag_skill)

    assert "ON CONFLICT (skill_name, version)" in source
    assert "skill_id = EXCLUDED.skill_id" not in source


def test_save_dag_panel_persists_original_definition_without_local_skill_resolution(monkeypatch):
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
    assert captured["definition_json"] == raw_definition


