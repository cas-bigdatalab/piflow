from pathlib import Path
from types import SimpleNamespace

from runtime import skill_manage
from runtime.skills_compat import install_deepagents_skills_refresh_compat


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
