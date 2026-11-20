"""Native model omission projection changes expression, never upstream values."""
import asyncio
from copy import deepcopy
from types import SimpleNamespace

from jsonschema import Draft202012Validator
import pytest

from ..capabilities import TASK, definition as native_definition, inputs, model_input_schema
from ..contracts import Server
from ..mcp import MCPGateway, Tool


def definition(field, *, required=(), **clauses):
    return {"type": "object", "properties": {"container": field}, "required": list(required), **clauses}


@pytest.mark.parametrize("field", [
    {"type": ["string", "null"], "minLength": 1, "default": None, "examples": [None, "provider-id"]},
    {"anyOf": [{"type": "string", "minLength": 2}, {"type": "integer", "minimum": 0}, {"type": "null"}], "default": None},
])
def test_optional_default_null_is_expressed_by_omission_without_value_coercion(field):
    original = definition(field)
    untouched = deepcopy(original)
    projected = model_input_schema(original)
    assert original == untouched and projected != original
    before = Draft202012Validator(original)
    after = Draft202012Validator(projected)
    assert before.is_valid({}) and after.is_valid({})
    assert before.is_valid({"container": None}) and not after.is_valid({"container": None})
    assert "default" not in projected["properties"]["container"]
    assert None not in projected["properties"]["container"].get("examples", [])
    for value in ("None", "root", "literal-id", "", -1, 0, True, [], {}):
        assert after.is_valid({"container": value}) == before.is_valid({"container": value})
    tool = Tool("arbitrary", "children", "Children", original, {}, {})
    assert inputs(tool, {}) == {"container": None}
    assert inputs(tool, {"container": "None"}) == {"container": "None"}


@pytest.mark.parametrize("value", [
    definition({"type": ["string", "null"], "default": None}, required=["container"]),
    definition({"type": "null", "default": None}),
    definition({"anyOf": [{"type": "null"}], "default": None}),
    definition({"type": ["string", "null"]}),
    definition({"type": ["string", "null"], "default": "provider-id"}),
    definition({"type": "string", "default": None}),
    definition({"$ref": "#/$defs/Parent", "default": None}),
    definition({"anyOf": [{}, {"type": "null"}], "default": None}),
    definition({"type": ["string", "null"], "default": None}, allOf=[{"required": ["container"]}]),
    definition({"type": ["string", "null"], "default": None}, dependentRequired={"mode": ["container"]}),
    definition({"type": ["string", "null"], "default": None}, minProperties=1),
    definition({"type": ["string", "null"], "default": None}, patternProperties={"^container$": {"type": "null"}}),
    definition({"type": ["string", "null"], "default": None}, anyOf=[{"required": ["container"]}, {}]),
    definition({"type": ["string", "null"], "default": None}, **{"$ref": "#/$defs/Arguments"}),
    definition({"anyOf": [{"$ref": "#/$defs/Parent"}, {"type": "null"}], "default": None}),
    definition({"type": ["string", "null"], "const": None, "default": None}),
    definition({"type": ["string", "null"], "enum": [None], "default": None}),
])
def test_required_null_only_and_complex_upstream_schemas_are_unchanged(value):
    assert model_input_schema(value) == value


def test_projection_precedes_qa_conditions_and_runtime_uses_the_upstream_schema():
    schema = definition({"type": ["string", "null"], "default": None})
    tool = Tool("arbitrary", "children", "Children", schema, {}, {"piflow": {"qa": {"atomic": True}}})
    untouched = deepcopy(tool.schema)
    projected = native_definition(tool)["function"]["parameters"]
    assert "allOf" in projected and TASK in projected["properties"]
    assert projected["properties"]["container"]["type"] == ["string"]
    assert "default" not in projected["properties"]["container"]
    assert tool.schema == untouched
    assert inputs(tool, {TASK: {"complete_request": True}}) == {"container": None}
    assert inputs(tool, {"container": None}) == {"container": None}
    assert inputs(tool, {"container": "None"}) == {"container": "None"}


def test_actual_dispatch_accepts_explicit_null_omission_and_literal_strings_unchanged():
    async def run():
        calls = []
        class Client:
            async def __aenter__(self):
                return self
            async def __aexit__(self, *args):
                pass
            async def call_tool(self, name, arguments, **kwargs):
                calls.append(deepcopy(arguments))
                return SimpleNamespace(is_error=False, structured_content={"received": deepcopy(arguments)})

        schema = definition({"type": ["string", "null"], "default": None})
        tool = Tool("arbitrary", "children", "Children", schema, {}, {})
        gateway = MCPGateway({"arbitrary": Server("in-memory")}, client_factory=lambda *args, **kwargs: Client())
        async with gateway.session() as session:
            session.include([tool])
            advertised = session.definitions()[0]["function"]["parameters"]
            assert not Draft202012Validator(advertised).is_valid({"container": None})
            for supplied in ({}, {"container": None}, {"container": "None"}, {"container": "root"}):
                bound = inputs(tool, supplied)
                actual, output = await session.call(tool.alias, bound)
                assert actual.schema == schema and output.data == {"received": bound}
        assert calls == [{"container": None}, {"container": None}, {"container": "None"}, {"container": "root"}]
    asyncio.run(run())
