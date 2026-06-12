from agents.prompts import build_system_prompt
from runtime.subagent import (
    build_summary_route_prompt_block,
    build_conversation_summary_system_prompt,
    is_summary_route_marker,
    SUMMARY_ROUTE_MARKER,
)


def test_summary_route_marker_matches_exact_contract():
    assert is_summary_route_marker(SUMMARY_ROUTE_MARKER) is True
    assert is_summary_route_marker(f"  {SUMMARY_ROUTE_MARKER}\n") is True
    assert is_summary_route_marker("帮我总结一下我们刚才这段对话") is False


def test_summary_route_prompt_block_is_composable():
    prompt_block = build_summary_route_prompt_block()
    system_prompt = build_system_prompt(extra_sections=[prompt_block])

    assert "skill生成路由规则" in prompt_block
    assert SUMMARY_ROUTE_MARKER in prompt_block
    assert "只输出该标记" in prompt_block
    assert prompt_block in system_prompt


def test_summary_system_prompt_is_skill_generation_prompt():
    prompt = build_conversation_summary_system_prompt()

    assert "skill 生成 subagent" in prompt
    assert "生成 skill" in prompt
