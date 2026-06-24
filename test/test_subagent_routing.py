from agents.subagent.skill_creator.prompt import (
    SKILL_CREATOR_ROUTE_MARKER,
    build_skill_creator_route_prompt_block,
    build_skill_creator_system_prompt,
    is_skill_creator_route_marker,
)
from agents.prompts import build_system_prompt


def test_skill_creator_route_marker_matches_exact_contract():
    assert is_skill_creator_route_marker(SKILL_CREATOR_ROUTE_MARKER) is True
    assert is_skill_creator_route_marker(f"  {SKILL_CREATOR_ROUTE_MARKER}\n") is True
    assert is_skill_creator_route_marker("帮我总结一下我们刚才这段对话") is False


def test_skill_creator_route_prompt_block_is_composable():
    prompt_block = build_skill_creator_route_prompt_block()
    system_prompt = build_system_prompt(extra_sections=[prompt_block])

    assert "skill生成路由规则" in prompt_block
    assert SKILL_CREATOR_ROUTE_MARKER in prompt_block
    assert "只输出该标记" in prompt_block
    assert prompt_block in system_prompt


def test_skill_creator_system_prompt_is_skill_generation_prompt():
    prompt = build_skill_creator_system_prompt()

    assert "skill 生成 subagent" in prompt
    assert "生成 skill" in prompt
