#!/usr/bin/env python3
import shutil
import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from generate_piflow_skill import generate_skill_files, workspace_root, write_text


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


if __name__ == "__main__":
    unittest.main()
