#!/usr/bin/env python3
import json
import shutil
import subprocess
import tempfile
import types
import unittest
from pathlib import Path
import sys
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))

from generate_piflow_skill import (
    generate,
    generate_skill_files,
    register_generated_dag_skill,
    register_generating_skill,
    resolve_output_root,
    validate_runtime_command_contract,
    workspace_root,
    write_text,
)


class GenerateSkillFilesTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp(prefix="generate-skill-files-"))

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_missing_script_source_falls_back_to_template(self):
        output_root = self.temp_dir / "skills" / "generated"
        spec = {
            "name": "epub_metadata_cleaner",
            "description": "清洗 EPUB 元数据。",
            "input_params": [
                {"name": "input_dir", "type": "directory", "description": "输入目录", "required": True}
            ],
            "output_params": [
                {"name": "output_dir", "type": "directory", "description": "输出目录"}
            ],
            "script": {
                "path": "scripts/run_epub_metadata_cleanup.py",
                "source": "E:/tmp/epub_metadata_cleanup_script.py",
            },
        }

        result = generate_skill_files(spec, output_root, overwrite=False)

        script_path = output_root / "epub_metadata_cleaner" / "scripts" / "run_epub_metadata_cleanup.py"
        self.assertTrue(script_path.exists())
        self.assertIn("json.dumps", script_path.read_text(encoding="utf-8"))
        completed = subprocess.run(
            [sys.executable, str(script_path), "--input_dir", "input"],
            capture_output=True,
            check=True,
            text=True,
            encoding="utf-8",
        )
        self.assertEqual(json.loads(completed.stdout)["status"], "ok")
        self.assertEqual(result["skill_dir"], output_root.joinpath("epub_metadata_cleaner").as_posix())

    def test_missing_script_creates_executable_python_entrypoint(self):
        output_root = self.temp_dir / "skills" / "generated"
        spec = {
            "name": "plain_text_summarizer",
            "description": "Summarize text when a concise overview is needed.",
            "input_params": [
                {"name": "text", "type": "string", "description": "Input text", "required": True}
            ],
            "output_params": [
                {"name": "summary", "type": "string", "description": "Summary text"}
            ],
        }

        result = generate_skill_files(spec, output_root, overwrite=False)
        script_path = output_root / "plain_text_summarizer" / "scripts" / "run_plain_text_summarizer.py"
        skill_json = json.loads((output_root / "plain_text_summarizer" / "skill.json").read_text(encoding="utf-8"))

        self.assertTrue(script_path.is_file())
        self.assertEqual(skill_json["script_path"], "scripts/run_plain_text_summarizer.py")
        self.assertEqual(skill_json["entrypoint"], "python scripts/run_plain_text_summarizer.py")
        completed = subprocess.run(
            [sys.executable, str(script_path), "--text", "hello"],
            capture_output=True,
            check=True,
            text=True,
            encoding="utf-8",
        )
        self.assertEqual(json.loads(completed.stdout)["inputs"], {"text": "hello"})
        self.assertEqual(result["skill_dir"], output_root.joinpath("plain_text_summarizer").as_posix())

    def test_workspace_output_returns_workspace_relative_paths(self):
        skill_root = workspace_root() / "skills" / "generated"
        skill_dir = skill_root / "unit_test_public_path"
        if skill_dir.exists():
            shutil.rmtree(skill_dir, ignore_errors=True)
        self.addCleanup(lambda: shutil.rmtree(skill_dir, ignore_errors=True))

        spec = {
            "name": "unit_test_public_path",
            "description": "验证返回路径保持在 workspace 根内。",
            "input_params": [
                {"name": "input_path", "type": "string", "description": "输入路径", "required": True}
            ],
            "output_params": [
                {"name": "output_path", "type": "string", "description": "输出路径"}
            ],
            "script": {
                "path": "scripts/run_demo.py",
                "content": "#!/usr/bin/env python3\nprint('demo')\n",
            },
        }

        result = generate_skill_files(spec, skill_root, overwrite=False)

        self.assertEqual(result["skill_dir"], "skills/generated/unit_test_public_path")
        self.assertEqual(result["skill_md"], "skills/generated/unit_test_public_path/SKILL.md")
        self.assertEqual(result["skill_json"], "skills/generated/unit_test_public_path/skill.json")

    def test_explicit_command_template_must_match_input_params(self):
        output_root = self.temp_dir / "skills" / "generated"
        spec = {
            "name": "bad_font_converter",
            "description": "将 TTF 字体转换为 OTF，并故意提供错误的 command_template 用于回归测试。",
            "input_params": [
                {"name": "file_path", "type": "string", "description": "输入字体路径", "required": True},
                {"name": "output_path", "type": "string", "description": "输出字体路径", "required": True, "role": "output_data"},
            ],
            "output_params": [
                {"name": "output_path", "type": "binary_file", "description": "输出 OTF 文件", "role": "output_data"}
            ],
            "script": {
                "path": "scripts/run_bad_font_converter.py",
                "content": "#!/usr/bin/env python3\nprint('demo')\n",
            },
            "command_template": [
                "python",
                "{script_path}",
                "--input_path",
                "{input_path}",
                "--output_path",
                "{output_path}",
            ],
        }

        with self.assertRaisesRegex(
            ValueError,
            "parameter 'file_path' must match command_template tokens '--file_path' and '{file_path}'",
        ):
            generate_skill_files(spec, output_root, overwrite=False)

    def test_runtime_command_contract_uses_real_piflow_parser(self):
        skill_dir = self.temp_dir / "skills" / "generated" / "demo_contract"
        skill_dir.mkdir(parents=True, exist_ok=True)
        skill_json = skill_dir / "skill.json"
        skill_json.write_text(
            """{
  "name": "demo_contract",
  "version": "1.0.0",
  "description": "demo",
  "language": "python",
  "script_path": "scripts/run_demo.py",
  "entrypoint": "python scripts/run_demo.py",
  "input_params": [
    {"name": "file_path", "role": "input_data", "type": "string", "required": true, "description": "input"}
  ],
  "output_params": [],
  "command_template": ["python", "{script_path}", "--input_path", "{input_path}"]
}
""",
            encoding="utf-8",
        )

        with self.assertRaisesRegex(
            ValueError,
            "parameter 'file_path' must match command_template tokens '--file_path' and '{file_path}'",
        ):
            validate_runtime_command_contract(skill_json)

    def test_resolve_output_root_normalizes_legacy_workspace_prefixes(self):
        expected = workspace_root() / "skills" / "generated"

        self.assertEqual(resolve_output_root("skills/generated"), expected)
        self.assertEqual(resolve_output_root("workspace/skills/generated"), expected)
        self.assertEqual(resolve_output_root("flow-deepagents/workspace/skills/generated"), expected)
        self.assertEqual(resolve_output_root("workspace/skills"), expected)

    def test_resolve_output_root_rejects_nested_workspace_prefixes(self):
        with self.assertRaisesRegex(ValueError, "nested workspace prefixes"):
            resolve_output_root("workspace/workspace/skills/generated")

    def test_generated_skill_markdown_includes_dependency_install_guidance(self):
        output_root = self.temp_dir / "skills" / "generated"
        spec = {
            "name": "midi_demo_skill",
            "description": "Convert a MIDI file into another representation.",
            "input_params": [
                {"name": "input_file", "type": "string", "description": "Input MIDI file", "required": True}
            ],
            "output_params": [
                {"name": "output_file", "type": "string", "description": "Output text file", "role": "output_data"}
            ],
            "dependencies": ["Python 3", "`mido`"],
            "script": {
                "path": "scripts/run_midi_demo_skill.py",
                "content": "#!/usr/bin/env python3\nprint('demo')\n",
            },
        }

        result = generate_skill_files(spec, output_root, overwrite=False)
        skill_md = Path(result["skill_md"])
        if not skill_md.is_absolute():
            skill_md = workspace_root() / result["skill_md"]
        text = skill_md.read_text(encoding="utf-8")

        self.assertIn("## 安装依赖", text)
        self.assertIn("pip install mido", text)

    def test_generate_records_skill_for_provided_thread(self):
        output_root = self.temp_dir / "skills" / "generated"
        spec = {
            "name": "demo_skill",
            "description": "Demo skill.",
            "input_params": [],
            "output_params": [],
        }
        file_result = {
            "skill_dir": "skills/generated/demo_skill",
            "skill_md": "skills/generated/demo_skill/SKILL.md",
            "skill_json": "skills/generated/demo_skill/skill.json",
        }

        with patch("generate_piflow_skill.generate_skill_files", return_value=file_result), patch(
            "generate_piflow_skill.register_skill_artifacts", return_value={}
        ), patch("generate_piflow_skill.register_generated_dag_skill", return_value={}), patch(
            "generate_piflow_skill.register_generating_skill",
            return_value={"thread_id": "thread-123", "skill_name": "demo_skill"},
        ) as register_record:
            result = generate(spec, output_root, overwrite=False, thread_id="thread-123")

        register_record.assert_called_once_with("thread-123", "demo_skill", output_root / "demo_skill")
        self.assertEqual(result["generating_skill"]["thread_id"], "thread-123")

    def test_register_generating_skill_records_workspace_relative_path(self):
        skill_dir = workspace_root() / "skills" / "generated" / "fasta_fna_validator"
        captured = {}

        fake_module = types.SimpleNamespace(
            upsert_generating_skill=lambda skill_name, skill_path, *, thread_id="": captured.update(
                thread_id=thread_id,
                skill_name=skill_name,
                skill_path=skill_path,
            ) or {"thread_id": thread_id, "skill_name": skill_name, "skill_path": skill_path}
        )
        original_runtime_module = sys.modules.get("runtime.skill_manage")
        sys.modules["runtime.skill_manage"] = fake_module
        try:
            result = register_generating_skill("thread-123", "fasta_fna_validator", skill_dir)
        finally:
            if original_runtime_module is None:
                del sys.modules["runtime.skill_manage"]
            else:
                sys.modules["runtime.skill_manage"] = original_runtime_module

        self.assertEqual(captured, {
            "thread_id": "thread-123",
            "skill_name": "fasta_fna_validator",
            "skill_path": "skills/generated/fasta_fna_validator",
        })
        self.assertEqual(result["thread_id"], "thread-123")

    def test_register_generated_dag_skill_returns_registered_skill_id(self):
        skill_dir = self.temp_dir / "skills" / "generated" / "fasta_fna_validator"
        skill_dir.mkdir(parents=True, exist_ok=True)

        import types

        fake_module = types.SimpleNamespace(
            update_generated_dag_skills_in_database=lambda *, skill_dir: {
                "count": 1,
                "skills": [{"id": 1, "skill_id": "generated-skill-id"}],
            }
        )
        original_runtime_module = sys.modules.get("runtime.skill_manage")
        sys.modules["runtime.skill_manage"] = fake_module
        try:
            result = register_generated_dag_skill(skill_dir)
        finally:
            if original_runtime_module is None:
                del sys.modules["runtime.skill_manage"]
            else:
                sys.modules["runtime.skill_manage"] = original_runtime_module

        self.assertEqual(result["dag_skill_registration_count"], 1)
        self.assertEqual(result["dag_skill_id"], "generated-skill-id")


if __name__ == "__main__":
    unittest.main()
