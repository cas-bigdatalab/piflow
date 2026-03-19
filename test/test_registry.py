from pydantic import BaseModel

from tools.core.registry import ToolRegistry
from tools.core.base import ToolSpec



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