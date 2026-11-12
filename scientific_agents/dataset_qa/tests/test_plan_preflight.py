"""Validate what is known before running prerequisites; bind real values later."""
import asyncio
from copy import deepcopy
import json

import pytest

from mcp_servers.corpus_mcp import mcp
from ..contracts import QAError, Server
from ..dialogue import builtin_definitions
from ..execution import Execution
from ..mcp import MCPGateway
from ..plan_runtime import install_plan
from ..planning import Workflow
from ..service import DatasetQA
from .test_dataset_qa import Backend, definition, engine, session
from .test_decisions import BareDialogue
from .test_file_pipeline import files
from .test_workflow_input import compact_plan, generic_tools


def parameter_backend():
    backend = Backend()
    tool = definition("render", {
        "source": {"type": "string"}, "format": {"$ref": "#/$defs/format"},
        "size": {"$ref": "#/$defs/size"}, "precision": {"type": "integer"}}, ["source", "format", "size"])
    tool.inputSchema["$defs"] = {"format": {"enum": ["compact", "detailed"]},
        "size": {"type": "integer", "minimum": 1, "maximum": 10}}
    tool.inputSchema.update({"if": {"properties": {"format": {"const": "detailed"}}},
        "then": {"required": ["precision"]}})
    backend.catalog = {"data": [tool]}
    return backend


@pytest.mark.parametrize("arguments,path", [
    ({"format": "unknown", "size": 3}, ["format"]),
    ({"format": "compact", "size": True}, ["size"]),
    ({"format": "compact", "size": 20}, ["size"]),
    ({"format": "compact"}, []),
    ({"format": "compact", "size": 3, "extra": 1}, []),
])
def test_known_invalid_values_fail_without_resolving_deferred_source(arguments, path):
    async def run():
        backend = parameter_backend()
        async with backend.gateway().session() as tools:
            await tools.load("data")
            alias = next(iter(tools.loaded))
            with pytest.raises(QAError) as error:
                tools.validate(alias, arguments, deferred={"source"})
            assert error.value.code == "invalid_parameters"
            assert error.value.detail["path"] == path
            assert not backend.calls
    asyncio.run(run())


def test_partial_validation_keeps_local_refs_and_defers_cross_field_conditions():
    async def run():
        backend = parameter_backend()
        async with backend.gateway().session() as tools:
            await tools.load("data")
            alias = next(iter(tools.loaded))
            original = deepcopy(tools.loaded[alias].schema)
            assert tools.validate(alias, {"format": "detailed", "size": 3}, deferred={"source"})
            with pytest.raises(QAError):
                tools.validate(alias, {"source": "actual", "format": "detailed", "size": 3})
            assert tools.validate(alias, {"source": "actual", "format": "detailed", "size": 3, "precision": 2})
            with pytest.raises(QAError):
                tools.validate(alias, {"source": 123, "format": "compact", "size": 3})
            assert tools.loaded[alias].schema == original
            assert not backend.calls
    asyncio.run(run())


@pytest.mark.parametrize("invalid", ["tsv", True, None])
def test_invalid_export_rejected_before_query_and_plan_commit(engine, files, invalid):
    async def run():
        service = DatasetQA(engine, BareDialogue(), MCPGateway({"piflow-corpus": Server(mcp)}))
        try:
            async with service.gateway.session() as tools:
                await tools.load("piflow-corpus", query="PubChem CSV")
                workflow = compact_plan()
                workflow["steps"][-1]["arguments"]["format"] = invalid
                execution, saved = Execution(), {}
                with pytest.raises(QAError) as error:
                    await install_plan(service, "alice", session(service), Workflow.model_validate(workflow),
                        tools, execution, saved, {})
                assert error.value.code == "invalid_parameters"
                assert not files.requests and not files.writes
                assert not execution.operations.items and not saved
        finally:
            await service.close()
    asyncio.run(run())


def test_plan_review_retains_every_hidden_tools_business_schema_without_duplication():
    tools = generic_tools()
    execution = Execution()
    raw = builtin_definitions(True)
    before = DatasetQA._definitions([*raw, *[tool.definition() for tool in tools.loaded.values()
        if tool.alias in execution.actions(tools.loaded)]], tools, execution)
    review = DatasetQA._definitions(raw, tools, execution)
    def catalogue(definitions):
        remember = next(d["function"] for d in definitions if d["function"]["name"] == "remember")
        return json.loads(remember["description"].split("Catalogue: ", 1)[1])
    assert len(catalogue(before)) == 1
    assert {row["tool"] for row in catalogue(review)} == set(tools.loaded)
    assert all(row["arguments_schema"] == tools.loaded[row["tool"]].schema for row in catalogue(review))
