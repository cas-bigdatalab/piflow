import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from runtime.engine import AgentEngine


def test_run_uses_summary_subagent_when_user_requests_conversation_summary():
    engine = AgentEngine(agent=MagicMock())
    fake_workspace = MagicMock()
    fake_workspace.detect_changed_downloadables.return_value = []

    with patch.object(
        engine,
        "_prepare_request",
        return_value=(
            {
                "messages": [
                    {"role": "user", "content": "第一轮"},
                    {"role": "assistant", "content": "第二轮"},
                    {"role": "user", "content": "请总结对话"},
                ]
            },
            fake_workspace,
            {},
        ),
    ), patch.object(
        engine,
        "_run_summary_subagent",
        new=AsyncMock(return_value=("这是对话总结", {"total_tokens": 12})),
    ) as fake_summary_runner, patch(
        "runtime.engine.save_message"
    ) as fake_save_message:
        result = asyncio.run(
            engine.run(
                "请总结对话",
                thread_id="thread-1",
                user_id="user-1",
                request_id="req-1",
            )
        )

    assert result == "这是对话总结"
    fake_summary_runner.assert_awaited_once()
    fake_save_message.assert_called_once_with("user-1", "thread-1", "assistant", "这是对话总结")


def test_stream_chat_returns_subagent_events_for_conversation_summary():
    engine = AgentEngine(agent=MagicMock())
    fake_workspace = MagicMock()
    fake_workspace.detect_changed_downloadables.return_value = []

    async def fake_summary_runner(**kwargs):
        await kwargs["on_event"](
            {
                "type": "subagent_status",
                "request_id": kwargs["request_id"],
                "task_name": "conversation_summary",
                "stage": "running",
            }
        )
        await kwargs["on_event"](
            {
                "type": "subagent_message_delta",
                "request_id": kwargs["request_id"],
                "task_name": "conversation_summary",
                "delta": "总结片段",
                "content": "总结片段",
            }
        )
        return "最终总结", {"total_tokens": 9}

    async def collect_events():
        items = []
        async for event in engine.stream_chat(
            "请总结对话",
            thread_id="thread-2",
            user_id="user-2",
            request_id="req-2",
        ):
            items.append(event)
        return items

    with patch.object(
        engine,
        "_prepare_request",
        return_value=(
            {
                "messages": [
                    {"role": "user", "content": "A"},
                    {"role": "assistant", "content": "B"},
                    {"role": "user", "content": "请总结对话"},
                ]
            },
            fake_workspace,
            {},
        ),
    ), patch.object(
        engine,
        "_run_summary_subagent",
        new=AsyncMock(side_effect=fake_summary_runner),
    ), patch(
        "runtime.engine.save_message"
    ):
        events = asyncio.run(collect_events())

    event_types = [item["type"] for item in events]
    assert "status" in event_types
    assert "subagent_status" in event_types
    assert "subagent_message_delta" in event_types
    assert events[-1]["type"] == "done"
    assert events[-1]["content"] == "最终总结"
