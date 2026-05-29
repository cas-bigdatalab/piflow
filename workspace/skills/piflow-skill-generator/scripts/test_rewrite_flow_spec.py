#!/usr/bin/env python3
import json
import shutil
import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from rewrite_piflow_skill import restore_rewrite_spec_from_flow
from generate_piflow_skill import write_text


class RewriteFlowSpecTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp(prefix="rewrite-flow-spec-"))
        self.skill_dir = self.temp_dir / "skills" / "demo_skill"
        self.skill_dir.mkdir(parents=True, exist_ok=True)
        write_text(
            self.skill_dir / "SKILL.md",
            "---\nname: demo_skill\ndescription: 原始描述\nversion: 1.0.0\ninput_params: []\noutput_params: []\n---\n\n# Demo\n",
        )
        write_text(
            self.skill_dir / "skill.json",
            json.dumps(
                {
                    "name": "demo_skill",
                    "version": "1.0.0",
                    "description": "原始描述",
                    "language": "python",
                    "script_path": "scripts/run_demo.py",
                    "entrypoint": "python scripts/run_demo.py",
                    "input_params": [],
                    "output_params": [],
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
        )

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_restore_rewrite_spec_reuses_existing_name_and_adds_guidance(self):
        flow_summary = {
            "task_name": "优化后的演示流程",
            "task_description": "根据新流程调整脚本说明与输出结构。",
            "skill_name": "ignored_new_name",
            "skill_name_zh": "优化后的演示技能",
            "inputs": [
                {"name": "input_path", "type": "string", "description": "输入文件", "required": True}
            ],
            "outputs": [
                {"name": "output_path", "type": "json_file", "description": "输出 JSON"}
            ],
            "processing_steps": [
                "读取输入文件",
                "执行新的流程逻辑",
                "输出结构化结果"
            ],
        }

        spec = restore_rewrite_spec_from_flow(self.skill_dir, flow_summary)

        self.assertEqual(spec["name"], "demo_skill")
        self.assertEqual(spec["name_zh"], "优化后的演示技能")
        self.assertEqual(spec["description"], "根据新流程调整脚本说明与输出结构。")
        self.assertTrue(spec["metadata"]["rewrite_existing_skill"])
        self.assertEqual(spec["metadata"]["rewrite_target_skill"], "demo_skill")
        self.assertIn("如果当前 skill 已生成完成", "\n".join(spec["notes"]))


if __name__ == "__main__":
    unittest.main()
