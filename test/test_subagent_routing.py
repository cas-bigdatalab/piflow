from agents.subagent.skill_creator.prompt import (
    SKILL_CREATOR_ROUTE_MARKER,
    build_skill_creator_route_prompt_block,
    build_skill_creator_system_prompt,
    is_skill_creator_route_marker,
)
from agents.prompts import BASE_PROMPT_NEW, build_system_prompt


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
    assert "只允许输出以下四类信息" in prompt
    assert "不允许输出或扩写以下内容" in prompt
    assert "完整 `SKILL.md`" in prompt
    assert "完整 `skill.json`" in prompt
    assert "run_*.py" in prompt
    assert "处理链、编排链、后续 DAG 建议" in prompt
    assert "你必须停在收集单和追问" in prompt


def test_main_system_prompt_keeps_core_dag_constraints():
    prompt = build_system_prompt()

    assert "输入节点 → 业务节点 → 输出节点" in prompt
    assert "只能输出合法 JSON" in prompt
    assert "技能缺失时的引导规则" in prompt
    assert "只能通过构建 DAG 或进入 skill 流程推进" in prompt
    assert "不要为输出参数编造真实值" in prompt


def test_main_system_prompt_removes_known_conflicting_wording():
    assert "在生成DAG Workflow JSON的同时，需要适当加入引导用语" not in BASE_PROMPT_NEW
    assert "节点输入参数。" not in BASE_PROMPT_NEW


def test_main_system_prompt_disallows_direct_problem_solving_path():
    prompt = build_system_prompt()

    assert "直接解决链路" not in prompt
    assert "临时脚本" not in prompt
    assert "脚本方案" not in prompt
    assert "不要直接给出替代解决方案或临时流程绕过问题" in prompt


def test_main_system_prompt_disallows_self_executing_task_resolution():
    prompt = build_system_prompt()

    assert "不要当场自行解决任务" in prompt
    assert "不要当场直接处理任务" in prompt
    assert "切记不要自行执行并解决任务，不要自行调用工具处理" in prompt
