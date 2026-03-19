import pytest
from pydantic import BaseModel

from tools.core.base import ToolSpec
from tools.adapters.deepagents_adapter import DeepAgentsAdapter


class DummyArgs(BaseModel):
    text: str


class DummyRegistry:
    async def call_internal(self, name, args):
        return {"result": "ok"}


@pytest.mark.asyncio
async def test_deepagents_adapter_convert():

    spec = ToolSpec(
        name="test.tool",
        description="test tool",
        args_schema=DummyArgs,
    )

    registry = DummyRegistry()

    tool = DeepAgentsAdapter.to_deepagents_tool(spec, registry)

    assert tool.name == "test__tool"

    result = await tool.ainvoke({"text": "hello"})

    assert result == {"result": "ok"}