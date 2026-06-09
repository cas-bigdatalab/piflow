import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from agents.factory import AgentFactory
from runtime.engine import AgentEngine
from tools.core.registry import registry


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
    ) as fake_summary_runner, patch.object(
        engine,
        "_should_use_summary_subagent",
        new=AsyncMock(return_value=True),
    ), patch(
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
    ), patch.object(
        engine,
        "_should_use_summary_subagent",
        new=AsyncMock(return_value=True),
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


def test_create_subagent_does_not_reregister_builtin_tools():
    fake_settings = SimpleNamespace(
        llm=SimpleNamespace(
            provider="openai",
            model="fake-model",
            temperature=0,
        ),
        providers=SimpleNamespace(
            openai=SimpleNamespace(
                base_url="http://example.com/v1",
                api_key_env=None,
            )
        ),
    )

    registry.clear()

    try:
        with patch("agents.factory.get_settings", return_value=fake_settings), patch(
            "agents.factory.ChatOpenAI", return_value=MagicMock(name="fake_llm")
        ), patch(
            "agents.factory.create_deep_agent",
            side_effect=[MagicMock(name="main_agent"), MagicMock(name="sub_agent")],
        ) as fake_create_deep_agent, patch(
            "agents.factory.WorkspaceManager"
        ) as fake_workspace_manager, patch.dict(
            "os.environ",
            {"LLM_API_KEY": "test-key"},
            clear=False,
        ):
            fake_workspace_manager.return_value.ensure_workspace.return_value = None

            main_agent = AgentFactory.create_agent()
            sub_agent = AgentFactory.create_subagent(
                system_prompt_override="summary prompt",
                context_text="ctx",
            )

        assert main_agent is not None
        assert sub_agent is not None
        assert fake_create_deep_agent.call_count == 2
        assert registry.has("shell.exec_shell") is True
        assert len(registry.list_records()) == 1
    finally:
        registry.clear()
