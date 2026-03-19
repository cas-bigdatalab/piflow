import pytest

from runtime.engine import AgentEngine
from tools.core.registry import registry


@pytest.mark.asyncio
async def test_engine_load_skills():

    engine = AgentEngine()

    await engine.initialize()

    tools = registry.list_records()

    # 至少有一个 tool
    assert len(tools) >= 1

    # 验证 tool name
    tool_names = [t.spec.name for t in tools]

    assert "report.generate_template" in tool_names