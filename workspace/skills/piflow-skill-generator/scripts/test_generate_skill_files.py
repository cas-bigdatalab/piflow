#!/usr/bin/env python3
import shutil
import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from generate_piflow_skill import (
    generate_skill_files,
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
        self.assertIn("NotImplementedError", script_path.read_text(encoding="utf-8"))
        self.assertEqual(result["skill_dir"], output_root.joinpath("epub_metadata_cleaner").as_posix())

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


if __name__ == "__main__":
    unittest.main()
