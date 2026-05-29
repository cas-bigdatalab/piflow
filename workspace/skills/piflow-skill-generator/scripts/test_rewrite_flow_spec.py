#!/usr/bin/env python3
import json
import shutil
import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from rewrite_piflow_skill import restore_rewrite_spec_from_flow, read_rewrite_input
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
                    "input_params": [
                        {
                            "name": "existing_input",
                            "role": "input_data",
                            "type": "string",
                            "required": True,
                            "description": "已有输入",
                        }
                    ],
                    "output_params": [
                        {
                            "name": "existing_output",
                            "role": "output_data",
                            "type": "json_file",
                            "description": "已有输出",
                        }
                    ],
                    "category": "existing_category",
                    "tag": "清洗",
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

    def test_restore_rewrite_spec_preserves_existing_contract_when_flow_is_partial(self):
        flow_summary = {
            "task_name": "仅补充说明",
            "task_description": "只调整描述，不改输入输出。",
        }

        spec = restore_rewrite_spec_from_flow(self.skill_dir, flow_summary)

        self.assertEqual(spec["name"], "demo_skill")
        self.assertEqual(spec["input_params"][0]["name"], "existing_input")
        self.assertEqual(spec["output_params"][0]["name"], "existing_output")
        self.assertEqual(spec["script_path"], "scripts/run_demo.py")
        self.assertEqual(spec["category"], "existing_category")
        self.assertEqual(spec["tag"], "清洗")

    def test_read_rewrite_input_rejects_spec_and_flow_together(self):
        spec_path = self.temp_dir / "rewrite-spec.json"
        flow_path = self.temp_dir / "rewrite-flow.json"
        write_text(spec_path, json.dumps({"name": "ignored", "description": "desc", "input_params": [], "output_params": []}, ensure_ascii=False))
        write_text(flow_path, json.dumps({"task_name": "flow"}, ensure_ascii=False))

        with self.assertRaisesRegex(ValueError, "provide either spec_path or flow_path, not both"):
            read_rewrite_input(
                skill_dir=self.skill_dir,
                spec_path=spec_path,
                flow_path=flow_path,
            )


if __name__ == "__main__":
    unittest.main()
