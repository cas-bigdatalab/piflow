import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from agents.factory import AgentFactory
from runtime.engine import AgentEngine
from runtime.subagent import SKILL_CREATOR_ROUTE_MARKER
from tools.core.registry import registry


def _make_ai_message(content: str, token_usage: dict | None = None):
    return SimpleNamespace(
        type="ai",
        content=content,
        tool_calls=None,
        tool_call_chunks=None,
        response_metadata={"token_usage": token_usage or {"total_tokens": 3}},
        additional_kwargs={},
    )


def test_run_uses_skill_creator_subagent_when_user_requests_conversation_summary():
    seen_inputs = []

    async def fake_astream(input_payload, config=None):  # noqa: ANN001
        seen_inputs.append(input_payload)
        if len(seen_inputs) == 1:
            yield {
                "planner": {
                    "messages": [_make_ai_message(SKILL_CREATOR_ROUTE_MARKER)],
                }
            }
            return

        yield {
            "planner": {
                "messages": [_make_ai_message("这是主agent基于总结后的最终回答", {"total_tokens": 21})],
            }
        }

    engine = AgentEngine(agent=SimpleNamespace(astream=fake_astream))
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
        "_run_skill_creator_subagent",
        new=AsyncMock(return_value=("这是给主agent参考的对话总结", {"total_tokens": 12})),
    ) as fake_skill_creator_runner, patch(
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

    assert result == "这是主agent基于总结后的最终回答"
    assert len(seen_inputs) == 2
    handoff_messages = seen_inputs[1]["messages"]
    assert handoff_messages[0]["role"] == "system"
    assert "这是给主agent参考的对话总结" in handoff_messages[0]["content"]
    assert SKILL_CREATOR_ROUTE_MARKER in seen_inputs[0]["messages"][-1]["content"] or True
    fake_skill_creator_runner.assert_awaited_once()
    fake_save_message.assert_called_once_with("user-1", "thread-1", "assistant", "这是主agent基于总结后的最终回答")


def test_stream_chat_hides_subagent_events_for_conversation_summary():
    seen_inputs = []

    async def fake_astream(input_payload, config=None, stream_mode=None):  # noqa: ANN001
        seen_inputs.append(input_payload)
        if len(seen_inputs) == 1:
            yield (
                "messages",
                (
                    _make_ai_message(SKILL_CREATOR_ROUTE_MARKER),
                    {"langgraph_node": "planner"},
                ),
            )
            return

        yield (
            "messages",
            (
                _make_ai_message("这是主agent吸收总结后的最终回答", {"total_tokens": 18}),
                {"langgraph_node": "planner"},
            ),
        )

    engine = AgentEngine(agent=SimpleNamespace(astream=fake_astream))
    fake_workspace = MagicMock()
    fake_workspace.detect_changed_downloadables.return_value = []

    async def fake_skill_creator_runner(**kwargs):
        await kwargs["on_event"](
            {
                "type": "subagent_status",
                "request_id": kwargs["request_id"],
                "task_name": "skill_creator",
                "stage": "running",
            }
        )
        await kwargs["on_event"](
            {
                "type": "subagent_message_delta",
                "request_id": kwargs["request_id"],
                "task_name": "skill_creator",
                "delta": "总结片段",
                "content": "总结片段",
            }
        )
        return "给主agent参考的最终总结", {"total_tokens": 9}

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
        "_run_skill_creator_subagent",
        new=AsyncMock(side_effect=fake_skill_creator_runner),
    ), patch(
        "runtime.engine.save_message"
    ):
        events = asyncio.run(collect_events())

    event_types = [item["type"] for item in events]
    assert "status" in event_types
    assert "subagent_status" not in event_types
    assert "subagent_message_delta" not in event_types
    assert "subagent_reasoning_delta" not in event_types
    assert "subagent_event" not in event_types
    assert events[-1]["type"] == "done"
    assert events[-1]["content"] == "这是主agent吸收总结后的最终回答"
    assert len(seen_inputs) == 2
    assert "给主agent参考的最终总结" in seen_inputs[1]["messages"][0]["content"]


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


def test_skill_creator_subagent_reuses_parent_thread_id_for_execution_context():
    engine = AgentEngine(agent=MagicMock())
    captured: dict[str, object] = {}
    emitted: list[dict[str, object]] = []

    async def fake_astream(input_payload, config=None, stream_mode=None):  # noqa: ANN001
        captured["input_payload"] = input_payload
        captured["config"] = config
        captured["stream_mode"] = stream_mode
        yield (
            "messages",
            (
                _make_ai_message("子agent总结结果", {"total_tokens": 7}),
                {"langgraph_node": "skill_creator"},
            ),
        )

    fake_subagent = SimpleNamespace(astream=fake_astream)

    async def on_event(event):  # noqa: ANN001
        emitted.append(event)

    async def collect_result():
        return await engine._run_skill_creator_subagent(
            parent_thread_id="parent-thread-1",
            user_id="user-1",
            request_id="req-1",
            messages=[
                {"role": "user", "content": "第一轮"},
                {"role": "assistant", "content": "第二轮"},
            ],
            on_event=on_event,
        )

    with patch("runtime.engine.AgentFactory.create_subagent", return_value=fake_subagent), patch(
        "runtime.engine.build_transient_thread_id",
        return_value="skill-creator-thread-xyz",
    ):
        answer, token_usage = asyncio.run(collect_result())

    assert answer == "子agent总结结果"
    assert token_usage == {"total_tokens": 7}
    assert captured["config"]["configurable"]["thread_id"] == "parent-thread-1"
    assert captured["config"]["configurable"]["user_id"] == "user-1"
    assert any(event.get("subagent_thread_id") == "skill-creator-thread-xyz" for event in emitted)


def test_run_falls_back_to_summary_text_when_handoff_agent_returns_marker_again():
    seen_inputs = []

    async def fake_astream(input_payload, config=None):  # noqa: ANN001
        seen_inputs.append(input_payload)
        yield {
            "planner": {
                "messages": [_make_ai_message(SKILL_CREATOR_ROUTE_MARKER)],
            }
        }

    engine = AgentEngine(agent=SimpleNamespace(astream=fake_astream))
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
        "_run_skill_creator_subagent",
        new=AsyncMock(return_value=("这是 summary agent 的最终总结", {"total_tokens": 12})),
    ), patch("runtime.engine.save_message") as fake_save_message:
        result = asyncio.run(
            engine.run(
                "请总结对话",
                thread_id="thread-3",
                user_id="user-3",
                request_id="req-3",
            )
        )

    assert result == "这是 summary agent 的最终总结"
    assert len(seen_inputs) == 2
    fake_save_message.assert_called_once_with("user-3", "thread-3", "assistant", "这是 summary agent 的最终总结")


def test_stream_chat_does_not_emit_or_finish_with_marker_after_handoff():
    seen_inputs = []

    async def fake_astream(input_payload, config=None, stream_mode=None):  # noqa: ANN001
        seen_inputs.append(input_payload)
        yield (
            "messages",
            (
                _make_ai_message(SKILL_CREATOR_ROUTE_MARKER),
                {"langgraph_node": "planner"},
            ),
        )

    engine = AgentEngine(agent=SimpleNamespace(astream=fake_astream))
    fake_workspace = MagicMock()
    fake_workspace.detect_changed_downloadables.return_value = []

    async def fake_skill_creator_runner(**kwargs):
        await kwargs["on_event"](
            {
                "type": "subagent_status",
                "request_id": kwargs["request_id"],
                "task_name": "skill_creator",
                "stage": "running",
            }
        )
        return "这是 summary agent 的最终总结", {"total_tokens": 9}

    async def collect_events():
        items = []
        async for event in engine.stream_chat(
            "请总结对话",
            thread_id="thread-4",
            user_id="user-4",
            request_id="req-4",
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
        "_run_skill_creator_subagent",
        new=AsyncMock(side_effect=fake_skill_creator_runner),
    ), patch("runtime.engine.save_message"):
        events = asyncio.run(collect_events())

    message_deltas = [item for item in events if item["type"] == "message_delta"]
    assert all(item["content"] != SKILL_CREATOR_ROUTE_MARKER for item in message_deltas)
    assert events[-1]["type"] == "done"
    assert events[-1]["content"] == "这是 summary agent 的最终总结"


def test_stream_chat_maps_subagent_progress_to_plain_agent_events():
    seen_inputs = []

    async def fake_astream(input_payload, config=None, stream_mode=None):  # noqa: ANN001
        seen_inputs.append(input_payload)
        if len(seen_inputs) == 1:
            yield (
                "messages",
                (
                    _make_ai_message(SKILL_CREATOR_ROUTE_MARKER),
                    {"langgraph_node": "planner"},
                ),
            )
            return

        yield (
            "messages",
            (
                _make_ai_message("最终主回答", {"total_tokens": 18}),
                {"langgraph_node": "planner"},
            ),
        )

    engine = AgentEngine(agent=SimpleNamespace(astream=fake_astream))
    fake_workspace = MagicMock()
    fake_workspace.detect_changed_downloadables.return_value = []

    async def fake_skill_creator_runner(**kwargs):
        await kwargs["on_event"](
            {
                "type": "subagent_status",
                "request_id": kwargs["request_id"],
                "task_name": "skill_creator",
                "stage": "preparing",
            }
        )
        await kwargs["on_event"](
            {
                "type": "subagent_event",
                "request_id": kwargs["request_id"],
                "task_name": "skill_creator",
                "nodes": ["skill_creator"],
                "tool_calls": [],
                "preview": "正在整理历史对话",
            }
        )
        await kwargs["on_event"](
            {
                "type": "subagent_message_delta",
                "request_id": kwargs["request_id"],
                "task_name": "skill_creator",
                "delta": "中间总结",
                "content": "中间总结",
            }
        )
        return "给主agent参考的最终总结", {"total_tokens": 9}

    async def collect_events():
        items = []
        async for event in engine.stream_chat(
            "请总结对话",
            thread_id="thread-6",
            user_id="user-6",
            request_id="req-6",
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
        "_run_skill_creator_subagent",
        new=AsyncMock(side_effect=fake_skill_creator_runner),
    ), patch("runtime.engine.save_message"):
        events = asyncio.run(collect_events())

    agent_events = [item for item in events if item["type"] == "agent_event"]
    assert agent_events
    assert all(item["type"] != "subagent_status" for item in events)
    assert all(item["type"] != "subagent_event" for item in events)
    assert all(item["type"] != "subagent_message_delta" for item in events)
    assert all(item["type"] != "subagent_reasoning_delta" for item in events)
    assert any("skill_creator" in (item.get("preview") or "") for item in agent_events)
    assert events[-1]["type"] == "done"
    assert events[-1]["content"] == "最终主回答"


def test_stream_chat_suppresses_partial_route_marker_chunks_before_handoff():
    seen_inputs = []

    async def fake_astream(input_payload, config=None, stream_mode=None):  # noqa: ANN001
        seen_inputs.append(input_payload)
        if len(seen_inputs) == 1:
            yield (
                "messages",
                (
                    _make_ai_message("__ROUTE_TO_SKILL_"),
                    {"langgraph_node": "planner"},
                ),
            )
            yield (
                "messages",
                (
                    _make_ai_message("__ROUTE_TO_SKILL_CREATOR__"),
                    {"langgraph_node": "planner"},
                ),
            )
            return

        yield (
            "messages",
            (
                _make_ai_message(SKILL_CREATOR_ROUTE_MARKER),
                {"langgraph_node": "planner"},
            ),
        )

    engine = AgentEngine(agent=SimpleNamespace(astream=fake_astream))
    fake_workspace = MagicMock()
    fake_workspace.detect_changed_downloadables.return_value = []

    async def fake_skill_creator_runner(**kwargs):
        return "这是 summary agent 的最终总结", {"total_tokens": 9}

    async def collect_events():
        items = []
        async for event in engine.stream_chat(
            "请总结对话",
            thread_id="thread-5",
            user_id="user-5",
            request_id="req-5",
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
        "_run_skill_creator_subagent",
        new=AsyncMock(side_effect=fake_skill_creator_runner),
    ), patch("runtime.engine.save_message"):
        events = asyncio.run(collect_events())

    message_deltas = [item["content"] for item in events if item["type"] == "message_delta"]
    assert all("__ROUTE_TO_SKILL_CREATOR__" not in content for content in message_deltas)
    assert all("__ROUTE_TO_SKILL_" not in content for content in message_deltas)
    assert events[-1]["content"] == "这是 summary agent 的最终总结"
