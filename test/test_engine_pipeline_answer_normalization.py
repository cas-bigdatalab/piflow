import json

from runtime.engine import _normalize_pipeline_answer_for_ui


def test_normalize_pipeline_answer_wraps_mixed_text_json_in_code_fence():
    dag = {
        "task": {"name": "demo", "description": "demo"},
        "nodes": [{"node_name": "n1", "skill_name": "source_stop", "params": {"file_path": "/tmp/a.csv", "output": ""}}],
    }
    raw = "先核对相关技能的参数定义，再直接生成可闭环DAG。" + json.dumps(dag, ensure_ascii=False)

    normalized = _normalize_pipeline_answer_for_ui(raw)

    assert normalized.startswith("先核对相关技能的参数定义")
    assert "```json" in normalized
    assert json.dumps(dag, ensure_ascii=False) in normalized


def test_normalize_pipeline_answer_keeps_pure_json_unchanged():
    dag = {
        "task": {"name": "demo", "description": "demo"},
        "nodes": [{"node_name": "n1", "skill_name": "source_stop", "params": {"file_path": "/tmp/a.csv", "output": ""}}],
    }
    raw = json.dumps(dag, ensure_ascii=False)

    assert _normalize_pipeline_answer_for_ui(raw) == raw


def test_normalize_pipeline_answer_keeps_non_pipeline_text_unchanged():
    raw = "这是普通说明文本，不包含可解析的 DAG。"

    assert _normalize_pipeline_answer_for_ui(raw) == raw


def test_normalize_pipeline_answer_produces_content_change_for_mixed_text_json():
    dag = {
        "task": {"name": "demo", "description": "demo"},
        "nodes": [{"node_name": "n1", "skill_name": "source_stop", "params": {"file_path": "/tmp/a.csv", "output": ""}}],
    }
    raw = "先检查一下参数。" + json.dumps(dag, ensure_ascii=False)

    normalized = _normalize_pipeline_answer_for_ui(raw)

    assert normalized != raw
    assert normalized.count("```json") == 1
