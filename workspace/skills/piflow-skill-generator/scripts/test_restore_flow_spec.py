#!/usr/bin/env python3
import json
import shutil
import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from generate_piflow_skill import restore_spec_from_flow, read_spec_input, write_text


class RestoreFlowSpecTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp(prefix="restore-flow-spec-"))

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_restore_spec_from_flow_builds_minimal_draft(self):
        flow_summary = {
            "task_name": "EPUB 元数据清洗",
            "task_description": "清洗一批 EPUB 的元数据并输出报告。",
            "skill_name": "epub_metadata_cleaner_from_flow",
            "skill_name_zh": "EPUB 元数据清洗算子",
            "category": "document_processing",
            "tag": "清洗",
            "inputs": [
                {
                    "name": "input_dir",
                    "type": "directory",
                    "description": "输入 EPUB 目录",
                    "required": True
                }
            ],
            "outputs": [
                {
                    "name": "report_dir",
                    "type": "directory",
                    "description": "输出报告目录"
                }
            ],
            "scripts": [
                {
                    "path": "scripts/run_epub_metadata_cleanup.py",
                    "source": "workspace/artifacts/epub_metadata_cleanup/run_epub_metadata_cleanup.py"
                }
            ],
            "processing_steps": [
                "扫描目录中的 EPUB 文件",
                "提取并规范标题、作者、语言、日期等字段",
                "输出清洗后的文件和报告"
            ],
            "success_evidence": {
                "summary_path": "workspace/outputs/epub_reports/summary.json"
            }
        }

        draft = restore_spec_from_flow(flow_summary)

        self.assertEqual(draft["name"], "epub_metadata_cleaner_from_flow")
        self.assertEqual(draft["name_zh"], "EPUB 元数据清洗算子")
        self.assertTrue(draft["description"])
        self.assertEqual(draft["input_params"][0]["name"], "input_dir")
        self.assertEqual(draft["output_params"][0]["name"], "report_dir")
        self.assertEqual(draft["scripts"][0]["path"], "scripts/run_epub_metadata_cleanup.py")
        self.assertIn("processing_logic", draft)
        self.assertIn("metadata", draft)
        self.assertEqual(draft["metadata"]["restored_from_flow"], True)

    def test_read_spec_input_supports_flow_summary(self):
        flow_path = self.temp_dir / "flow.json"
        output_path = self.temp_dir / "restored.json"
        flow_summary = {
            "task_name": "PDF 元数据提取",
            "task_description": "提取 PDF 元数据并输出 JSON。",
            "skill_name": "pdf_metadata_extract_restored",
            "skill_name_zh": "PDF 元数据提取回调算子",
            "inputs": [
                {"name": "input_path", "type": "string", "description": "输入 PDF", "required": True}
            ],
            "outputs": [
                {"name": "output_path", "type": "json_file", "description": "输出 JSON"}
            ]
        }
        write_text(flow_path, json.dumps(flow_summary, ensure_ascii=False, indent=2))

        spec = read_spec_input(flow_path=flow_path, restored_spec_path=output_path)

        self.assertEqual(spec["name"], "pdf_metadata_extract_restored")
        self.assertTrue(output_path.exists())

    def test_restore_spec_supports_alias_fields_and_dag_nodes(self):
        flow_summary = {
            "task": {
                "name": "CSV 清洗流程",
                "description": "对 CSV 文件执行标准清洗并输出结果。"
            },
            "name_zh": "CSV 清洗回调算子",
            "input_params": [
                {"name": "input_path", "type": "string", "description": "输入 CSV", "required": True}
            ],
            "output_params": [
                {"name": "output_path", "type": "csv_file", "description": "输出 CSV"}
            ],
            "script": {
                "path": "scripts/run_csv_cleanup.py",
                "content": "print('demo')\n"
            },
            "steps": [
                "读取 CSV 文件",
                "执行清洗步骤",
                "写出结果文件"
            ],
            "nodes": [
                {"node_name": "输入文件", "skill_name": "source_stop"},
                {"node_name": "空格清洗", "skill_name": "trim_spaces"},
                {"node_name": "输出文件", "skill_name": "sink_stop"}
            ],
            "validation": {
                "status": "passed",
                "artifacts": ["workspace/outputs/result.csv"]
            },
            "metadata": {
                "entry_chain": "callback_distillation"
            }
        }

        draft = restore_spec_from_flow(flow_summary)

        self.assertEqual(draft["title"], "CSV 清洗流程")
        self.assertEqual(draft["name_zh"], "CSV 清洗回调算子")
        self.assertEqual(draft["input_params"][0]["name"], "input_path")
        self.assertEqual(draft["output_params"][0]["name"], "output_path")
        self.assertEqual(draft["scripts"][0]["path"], "scripts/run_csv_cleanup.py")
        self.assertTrue(any("节点" in step or "source_stop" in step for step in draft["processing_logic"]))
        self.assertEqual(draft["metadata"]["restored_from_flow"], True)


if __name__ == "__main__":
    unittest.main()
