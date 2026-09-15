from __future__ import annotations

import os
from pathlib import Path

import pytest


@pytest.mark.integration
def test_submit_frontend_dag_with_real_task_id():
    # if os.getenv("RUN_REAL_PIFLOW_TEST") != "1":
    #     pytest.skip("set RUN_REAL_PIFLOW_TEST=1 to enable this integration test")
    #
    # create_user_id = os.getenv("TEST_DAG_CREATE_USER_ID")
    # dag_task_id = os.getenv("TEST_DAG_TASK_ID")
    # if not create_user_id or not dag_task_id:
    #     pytest.skip("set TEST_DAG_CREATE_USER_ID and TEST_DAG_TASK_ID before running this test")
    #
    # pytest.importorskip("cn.piflow.core.flow_bean")
    # pytest.importorskip("cn.piflow.core.frontend_dag_converter")
    # pytest.importorskip("cn.piflow.core.runner")

    from runtime.piflow_adapter import submit_frontend_dag
    from services.dag_panel_service import get_panel_dag_json

    definition_json = get_panel_dag_json(
        create_user_id="3b558b3661da4c40b251f646ca442936",
        dag_task_id="c7d4270e429f4ea283742ae634ed5cc8",
    )

    assert definition_json is not None, f"dag definition not found: c7d4270e429f4ea283742ae634ed5cc8"

    process = submit_frontend_dag(definition_json=definition_json)

    assert process is not None
    assert hasattr(process, "pid")
    assert process.pid() is not None


@pytest.mark.integration
def test_submit_frontend_dag_for_pdf_extract_json():
    from runtime.piflow_adapter import submit_frontend_dag

    project_root = Path(__file__).resolve().parents[1]
    workspace_root = project_root / "workspace"
    input_pdf = workspace_root / "temp" / "Akcay.pdf"
    if not input_pdf.exists():
        pytest.skip(f"input pdf not found: {input_pdf}")

    definition_json = {
        "dsl_version": "1.0",
        "task": {
            "dag_task_id": "f52e0d0a26974687a7d95d888ac8ccb5",
            "dag_task_name": "PDF 文档元数据与文本提取",
            "description": "提取 PDF 文档的元数据信息并提取文本内容",
            "message_id": "1048",
        },
        "nodes": [
            {
                "node_id": "node-0",
                "node_name": "输入 PDF 文件",
                "node_type": "default",
                "icon_path": "",
                "skill": {
                    "skill_id": "cn.piflow.piflow_engine.local.source_file_stop.SourceFileStop",
                    "version": "1.0",
                },
                "position": {"x": 100, "y": 200},
                "input_params": [
                    {
                        "param_name": "file_path",
                        "param_value": "/temp/Akcay.pdf",
                        "value_mode": "manual",
                        "binding_id": "",
                    },
                    {
                        "param_name": "output",
                        "param_value": "",
                        "value_mode": "manual",
                        "binding_id": "",
                    },
                ],
                "out_params": [],
            },
            {
                "node_id": "node-1",
                "node_name": "提取元数据",
                "node_type": "default",
                "icon_path": "/storage/skills/pdf_metadata_extract.png",
                "skill": {
                    "skill_id": "dc5b6b40a4874fad92a7dfd4aecadf75",
                    "version": "1.0",
                },
                "position": {"x": 300, "y": 200},
                "input_params": [
                    {
                        "param_name": "input_path",
                        "param_value": "output",
                        "value_mode": "reference",
                        "binding_id": "",
                    },
                    {
                        "param_name": "output_path",
                        "param_value": "workspace/outputs/Akcay_metadata.json",
                        "value_mode": "manual",
                        "binding_id": "",
                    },
                ],
                "out_params": [
                    {
                        "param_name": "output",
                        "param_type": "json_file",
                    }
                ],
            },
            {
                "node_id": "node-2",
                "node_name": "提取文本内容",
                "node_type": "default",
                "icon_path": "/storage/skills/pdf_text_extract.png",
                "skill": {
                    "skill_id": "f2a5ae6b46f441d49e462092f7b27f84",
                    "version": "1.0",
                },
                "position": {"x": 500, "y": 200},
                "input_params": [
                    {
                        "param_name": "input_path",
                        "param_value": "output",
                        "value_mode": "reference",
                        "binding_id": "",
                    },
                    {
                        "param_name": "output_path",
                        "param_value": "workspace/outputs/Akcay_text.txt",
                        "value_mode": "manual",
                        "binding_id": "",
                    },
                    {
                        "param_name": "pages",
                        "param_value": "",
                        "value_mode": "manual",
                        "binding_id": "",
                    },
                ],
                "out_params": [
                    {
                        "param_name": "output",
                        "param_type": "text_file",
                    }
                ],
            },
            {
                "node_id": "node-3",
                "node_name": "输出元数据文件",
                "node_type": "default",
                "icon_path": "",
                "skill": {
                    "skill_id": "cn.piflow.piflow_engine.local.file_save_stop.FileSaveStop",
                    "version": "1.0",
                },
                "position": {"x": 700, "y": 200},
                "input_params": [
                    {
                        "param_name": "input",
                        "param_value": "output",
                        "value_mode": "reference",
                        "binding_id": "",
                    },
                    {
                        "param_name": "path",
                        "param_value": "workspace/outputs/Akcay_metadata.json",
                        "value_mode": "manual",
                        "binding_id": "",
                    },
                    {
                        "param_name": "overwrite",
                        "param_value": "true",
                        "value_mode": "manual",
                        "binding_id": "",
                    },
                ],
                "out_params": [],
            },
            {
                "node_id": "node-4",
                "node_name": "输出文本文件",
                "node_type": "default",
                "icon_path": "",
                "skill": {
                    "skill_id": "cn.piflow.piflow_engine.local.file_save_stop.FileSaveStop",
                    "version": "1.0",
                },
                "position": {"x": 900, "y": 200},
                "input_params": [
                    {
                        "param_name": "input",
                        "param_value": "output",
                        "value_mode": "reference",
                        "binding_id": "",
                    },
                    {
                        "param_name": "path",
                        "param_value": "workspace/outputs/Akcay_text.txt",
                        "value_mode": "manual",
                        "binding_id": "",
                    },
                    {
                        "param_name": "overwrite",
                        "param_value": "true",
                        "value_mode": "manual",
                        "binding_id": "",
                    },
                ],
                "out_params": [],
            },
        ],
        "edges": [
            {"edge_id": "edge-0", "from_node_id": "node-0", "to_node_id": "node-1"},
            {"edge_id": "edge-1", "from_node_id": "node-1", "to_node_id": "node-2"},
            {"edge_id": "edge-2", "from_node_id": "node-2", "to_node_id": "node-3"},
            {"edge_id": "edge-3", "from_node_id": "node-3", "to_node_id": "node-4"},
        ],
        "bindings": [
            {
                "binding_id": "binding-1-input_path",
                "from_node_id": "node-0",
                "from_param_name": "output",
                "to_node_id": "node-1",
                "to_param_name": "input_path",
            },
            {
                "binding_id": "binding-2-input_path",
                "from_node_id": "node-1",
                "from_param_name": "output",
                "to_node_id": "node-2",
                "to_param_name": "input_path",
            },
            {
                "binding_id": "binding-3-input",
                "from_node_id": "node-2",
                "from_param_name": "output",
                "to_node_id": "node-3",
                "to_param_name": "input",
            },
            {
                "binding_id": "binding-4-input",
                "from_node_id": "node-3",
                "from_param_name": "output",
                "to_node_id": "node-4",
                "to_param_name": "input",
            },
        ],
    }

    metadata_output = workspace_root / "workspace" / "outputs" / "Akcay_metadata.json"
    text_output = workspace_root / "workspace" / "outputs" / "Akcay_text.txt"

    for path in (metadata_output, text_output):
        if path.exists():
            path.unlink()

    process = submit_frontend_dag(definition_json=definition_json)
    process.await_termination(timeout=30 * 2000)

    assert process.pid() is not None
    assert metadata_output.exists(), f"metadata output not found: {metadata_output}"
    assert text_output.exists(), f"text output not found: {text_output}"
    assert metadata_output.stat().st_size > 0
    assert text_output.stat().st_size > 0
