"""Tolerant MCP inputs keep dispatch, preflight and contract boundaries aligned."""
import asyncio
from copy import deepcopy

import pytest

from ..contracts import QAError
from .test_dataset_qa import Backend, definition


@pytest.mark.parametrize("isolated", [False, True])
def test_dispatch_repairs_numeric_fields_and_preserves_identifiers_and_extra_data(isolated):
    async def run():
        backend = Backend()
        item = definition("inspect", {
            "count": {"type": "integer", "minimum": 1, "maximum": 10},
            "scale": {"type": "number"},
            "optional": {"anyOf": [{"type": "integer"}, {"type": "null"}]},
            "record_id": {"type": "string"},
            "filters": {"type": "array", "items": {"type": "object", "properties": {
                "threshold": {"type": "number"}}}},
        })
        item.inputSchema["additionalProperties"] = True
        backend.catalog = {"data": [item]}
        arguments = {"count": " 5 ", "scale": "1.25", "optional": "2", "record_id": "00017",
            "filters": [{"threshold": "2e2", "extension": "003"}], "extra": {"value": "9"}}
        expected = {**arguments, "count": 5, "scale": 1.25, "optional": 2,
            "filters": [{"threshold": 200, "extension": "003"}]}
        async with backend.gateway().session() as tools:
            await tools.load("data")
            alias = next(iter(tools.loaded))
            dispatch = tools.call_isolated if isolated else tools.call
            await dispatch(alias, arguments)
            assert backend.calls == [("data", "inspect", expected)]
            assert arguments == expected
    asyncio.run(run())


@pytest.mark.parametrize("field,value,expected", [
    ({"type": ["integer", "null"]}, "5", 5),
    ({"type": ["integer", "null"]}, None, None),
    ({"type": "number"}, "9007199254740993", 9007199254740993),
    ({"type": "number"}, "-1.25e-2", -0.0125),
    ({"type": ["integer", "string"]}, "5", "5"),
    ({"anyOf": [{"type": "integer"}, {"type": "string"}]}, "005", "005"),
])
def test_nullable_numbers_and_ambiguous_string_values_follow_advertised_types(field, value, expected):
    async def run():
        backend = Backend()
        backend.catalog = {"data": [definition("inspect", {"value": field})]}
        async with backend.gateway().session() as tools:
            await tools.load("data")
            await tools.call(next(iter(tools.loaded)), {"value": value})
        actual = backend.calls[0][2]["value"]
        assert actual == expected and type(actual) is type(expected)
    asyncio.run(run())


@pytest.mark.parametrize("value", [True, None, "5 records", "05", "1,000", "1.5", "0", "11",
    "NaN", "Infinity", "1e999999999999", "-1e999999999999"])
def test_unsafe_or_out_of_range_inputs_do_not_dispatch_or_mutate(value):
    async def run():
        backend = Backend()
        backend.catalog = {"data": [definition("inspect", {
            "count": {"type": "integer", "minimum": 1, "maximum": 10}}, ["count"])]}
        arguments = {"count": value}
        before = deepcopy(arguments)
        async with backend.gateway().session() as tools:
            await tools.load("data")
            with pytest.raises(QAError) as caught:
                await tools.call(next(iter(tools.loaded)), arguments)
            assert caught.value.code == "invalid_parameters"
        assert arguments == before and not backend.calls
    asyncio.run(run())


def test_repair_does_not_drop_unknown_fields_relax_conditions_or_fill_deferred_inputs():
    async def run():
        backend = Backend()
        item = definition("inspect", {"count": {"type": "integer"}, "reference": {"type": "string"},
            "format": {"type": "string", "enum": ["csv", "json"]}}, ["count", "reference"])
        item.inputSchema.update({"if": {"properties": {"count": {"minimum": 5}}}, "then": {"required": ["format"]}})
        backend.catalog = {"data": [item]}
        async with backend.gateway().session() as tools:
            await tools.load("data")
            alias = next(iter(tools.loaded))
            arguments = {"count": "5"}
            tools.validate(alias, arguments, deferred={"reference"})
            assert arguments == {"count": 5} and not backend.calls
            for invalid in [{"count": "5", "reference": "actual"},
                    {"count": "5", "reference": "actual", "format": "CSV"},
                    {"count": "5", "reference": "actual", "format": "csv", "typo": True}]:
                before = deepcopy(invalid)
                with pytest.raises(QAError):
                    await tools.call(alias, invalid)
                assert invalid == before and not backend.calls
            await tools.call(alias, {**arguments, "reference": "actual", "format": "csv"})
            assert backend.calls == [("data", "inspect", {"count": 5, "reference": "actual", "format": "csv"})]
    asyncio.run(run())
