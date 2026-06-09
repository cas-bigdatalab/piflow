import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from runtime.subagent import is_conversation_summary_request


def test_summary_route_returns_true_when_router_says_yes():
    fake_llm = SimpleNamespace(
        ainvoke=AsyncMock(return_value=SimpleNamespace(content="YES"))
    )

    with patch("runtime.subagent._build_router_llm", return_value=fake_llm):
        result = asyncio.run(
            is_conversation_summary_request("帮我总结一下我们刚才这段对话")
        )

    assert result is True


def test_summary_route_returns_false_when_router_says_no():
    fake_llm = SimpleNamespace(
        ainvoke=AsyncMock(return_value=SimpleNamespace(content="NO"))
    )

    with patch("runtime.subagent._build_router_llm", return_value=fake_llm):
        result = asyncio.run(
            is_conversation_summary_request("帮我总结这个 PDF 的内容")
        )

    assert result is False


def test_summary_route_fails_closed_when_router_errors():
    fake_llm = SimpleNamespace(ainvoke=AsyncMock(side_effect=RuntimeError("boom")))

    with patch("runtime.subagent._build_router_llm", return_value=fake_llm):
        result = asyncio.run(
            is_conversation_summary_request("总结一下当前对话")
        )

    assert result is False
