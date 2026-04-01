from pydantic import BaseModel
import pytest

from tools.core.registry import ToolRegistry
from tools.core.base import ToolSpec
from runtime.policy import Policy



class EchoArgs(BaseModel):
    text: str


def echo_tool(text: str):
    return text


def test_tool_registry_register_and_list():

    registry = ToolRegistry()

    spec = ToolSpec(
        name="test.echo",
        description="echo tool",
        args_schema=EchoArgs
    )

    registry.register(spec, echo_tool)

    tools = registry.list_records()

    assert len(tools) == 1
    assert tools[0].spec.name == "test.echo"


def test_tool_registry_get():

    registry = ToolRegistry()

    spec = ToolSpec(
        name="test.echo",
        description="echo tool",
        args_schema=EchoArgs
    )

    registry.register(spec, echo_tool)

    result = registry.get_record_by_internal("test.echo")

    assert result is not None
    assert result.spec.name == "test.echo"


@pytest.mark.asyncio
async def test_tool_registry_budget_is_per_request():
    registry = ToolRegistry(
        policy=Policy(
            total_call_budget=10,
            per_tool_budget={"test.echo": 1},
        )
    )

    spec = ToolSpec(
        name="test.echo",
        description="echo tool",
        args_schema=EchoArgs,
    )
    registry.register(spec, echo_tool)

    registry.begin_request()
    first = await registry.call_internal("test.echo", {"text": "a"})
    assert first.success is True

    with pytest.raises(RuntimeError, match="Tool budget exceeded for test.echo"):
        await registry.call_internal("test.echo", {"text": "b"})

    registry.begin_request()
    third = await registry.call_internal("test.echo", {"text": "c"})
    assert third.success is True
