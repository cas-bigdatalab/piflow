import asyncio
import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from runtime.engine import AgentEngine, _normalize_pipeline_answer_for_ui


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


def test_normalize_pipeline_answer_wraps_task_scoped_nodes_payload():
    dag = {
        "task": {
            "name": "demo",
            "description": "demo",
            "nodes": [
                {
                    "node_name": "n1",
                    "skill_name": "source_stop",
                    "params": {"file_path": "/tmp/a.csv", "output": ""},
                }
            ],
        }
    }
    raw = "下面是规划结果：" + json.dumps(dag, ensure_ascii=False)

    normalized = _normalize_pipeline_answer_for_ui(raw)

    assert normalized.startswith("下面是规划结果：")
    assert "```json" in normalized
    assert json.dumps(dag, ensure_ascii=False) in normalized


def _make_ai_message(content: str, token_usage: dict | None = None):
    return SimpleNamespace(
        type="ai",
        content=content,
        tool_calls=None,
        tool_call_chunks=None,
        response_metadata={"token_usage": token_usage or {"total_tokens": 3}},
        additional_kwargs={},
    )


def test_stream_chat_normalizes_pipeline_json_before_message_delta():
    dag = {
        "task": {"name": "demo", "description": "demo"},
        "nodes": [{"node_name": "n1", "skill_name": "source_stop", "params": {"file_path": "/tmp/a.csv", "output": ""}}],
    }
    raw = "我已为你生成该任务的完整 DAG 流程。\n" + json.dumps(dag, ensure_ascii=False)
    normalized = _normalize_pipeline_answer_for_ui(raw)

    async def fake_astream(input_payload, config=None, stream_mode=None):  # noqa: ANN001
        yield (
            "messages",
            (
                _make_ai_message(raw, {"total_tokens": 18}),
                {"langgraph_node": "planner"},
            ),
        )

    engine = AgentEngine(agent=SimpleNamespace(astream=fake_astream))
    fake_workspace = MagicMock()
    fake_workspace.detect_changed_downloadables.return_value = []

    async def collect_events():
        items = []
        async for event in engine.stream_chat(
            "生成一个 DAG",
            thread_id="thread-pipeline",
            user_id="user-pipeline",
            request_id="req-pipeline",
        ):
            items.append(event)
        return items

    with patch.object(
        engine,
        "_prepare_request",
        return_value=(
            {
                "messages": [
                    {"role": "user", "content": "生成一个 DAG"},
                ]
            },
            fake_workspace,
            {},
        ),
    ), patch("runtime.engine.save_message"):
        events = asyncio.run(collect_events())

    message_deltas = [item for item in events if item["type"] == "message_delta"]
    assert message_deltas
    assert message_deltas[-1]["content"] == normalized
    assert "```json" in message_deltas[-1]["content"]
    message_events = [item for item in events if item["type"] == "message"]
    assert message_events[-1]["content"] == normalized
    assert events[-1]["type"] == "done"
    assert events[-1]["content"] == normalized
