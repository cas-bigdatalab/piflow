"""Requested operations survive compilation, repair and deferred source binding."""
import asyncio
from copy import deepcopy

import pytest

from mcp_servers.corpus_mcp import mcp
from ..contracts import QAError, Server
from ..execution import Execution
from ..mcp import MCPGateway, Tool
from ..plan_runtime import compile_workflow, install_plan
from ..planning import Plan, Workflow, plan_input, plan_view, validate_revision
from ..service import DatasetQA
from .test_dataset_qa import engine, session
from .test_decisions import BareDialogue
from .test_file_pipeline import files
from .test_workflow_input import compact_plan, generic_tools


def declared_workflow():
    return Workflow(steps=[{"key": "fetch", "tool": "retrieve"},
        {"key": "convert", "tool": "transform", "object": "fetch",
         "arguments": {"encoding": "csv"}, "operation": "export", "output_format": "csv"}])


def test_intent_survives_compilation_editable_view_and_omitted_revision_fields():
    tools = generic_tools()
    plan = compile_workflow(declared_workflow(), tools)
    saved = {"spec": plan.model_dump(), "revision": 1, "operations": {"fetch": "op1", "convert": "op2"}}
    shown = plan_view(saved, Execution().operations)
    editable = plan_input(shown)
    assert editable.steps[-1].operation == "export"
    assert editable.steps[-1].output_format == "csv"
    assert compile_workflow(editable, tools, saved) == plan

    revised = declared_workflow().model_dump()
    revised["steps"][-1].pop("operation")
    revised["steps"][-1].pop("output_format")
    compiled = compile_workflow(Workflow.model_validate(revised), tools, saved)
    validate_revision(saved, compiled)
    assert compiled.steps[-1].operation == "export"
    assert compiled.steps[-1].output_format == "csv"


@pytest.mark.parametrize("field,value", [("operation", None), ("operation", "filter"),
    ("output_format", None), ("output_format", "jsonl")])
def test_revision_cannot_erase_or_replace_declared_intent(field, value):
    tools = generic_tools()
    original = compile_workflow(declared_workflow(), tools)
    revised = deepcopy(original.model_dump())
    revised["steps"][-1][field] = value
    with pytest.raises(QAError, match="操作目的和输出格式"):
        validate_revision({"spec": original.model_dump()}, Plan.model_validate(revised))


def test_intent_does_not_prevent_correcting_the_selected_tool():
    tools = generic_tools()
    original = compile_workflow(declared_workflow(), tools)
    source = next(tool for tool in tools.loaded.values() if tool.name == "transform")
    alternative = Tool(source.server, "alternate", source.description, deepcopy(source.schema),
        deepcopy(source.annotations), deepcopy(source.meta))
    tools.loaded[alternative.alias] = alternative
    revised = declared_workflow().model_dump()
    revised["steps"][-1]["tool"] = "alternate"
    compiled = compile_workflow(Workflow.model_validate(revised), tools, {"spec": original.model_dump()})
    validate_revision({"spec": original.model_dump()}, compiled)
    assert compiled.steps[-1].tool == alternative.alias
    assert compiled.steps[-1].operation == "export"


@pytest.mark.parametrize("operation,output_format,business_format", [
    ("filter", "csv", "csv"), ("export", "jsonl", "csv"), ("export", "csv", "jsonl")])
def test_incompatible_goal_rejected_before_prerequisite_dispatch(engine, files, operation, output_format, business_format):
    async def run():
        service = DatasetQA(engine, BareDialogue(), MCPGateway({"piflow-corpus": Server(mcp)}))
        try:
            async with service.gateway.session() as tools:
                await tools.load("piflow-corpus", query="PubChem CSV")
                workflow = compact_plan()
                workflow["steps"][-1].update(operation=operation, output_format=output_format)
                workflow["steps"][-1]["arguments"]["format"] = business_format
                execution, saved = Execution(), {}
                with pytest.raises(QAError) as error:
                    await install_plan(service, "alice", session(service), Workflow.model_validate(workflow),
                        tools, execution, saved, {})
                assert error.value.detail["phase"] == "plan_validation"
                assert error.value.detail["dispatched"] is False
                assert not files.requests and not files.writes
                assert not execution.operations.items and not saved
        finally:
            await service.close()
    asyncio.run(run())


def test_deferred_format_keeps_intent_without_requiring_a_placeholder(engine, files):
    async def run():
        service = DatasetQA(engine, BareDialogue(), MCPGateway({"piflow-corpus": Server(mcp)}))
        try:
            async with service.gateway.session() as tools:
                await tools.load("piflow-corpus", query="PubChem CSV")
                workflow = compact_plan()
                workflow["steps"][-1].update(operation="export", output_format="csv", arguments={},
                    inputs={"format": {"step": "query", "path": "/requested_format"}})
                execution, saved = Execution(), {}
                await install_plan(service, "alice", session(service), Workflow.model_validate(workflow),
                    tools, execution, saved, {})
                step = saved["plan"]["spec"]["steps"][-1]
                assert step["operation"] == "export" and step["output_format"] == "csv"
                assert step["arguments"] == {}
                assert not files.requests and not files.writes
        finally:
            await service.close()
    asyncio.run(run())


def test_old_saved_plan_without_optional_intent_keeps_revision_and_review(engine, files):
    async def run():
        service = DatasetQA(engine, BareDialogue(), MCPGateway({"piflow-corpus": Server(mcp)}))
        try:
            async with service.gateway.session() as tools:
                await tools.load("piflow-corpus", query="PubChem CSV")
                execution, saved = Execution(), {}
                sid = session(service)
                await install_plan(service, "alice", sid, Workflow.model_validate(compact_plan()), tools,
                    execution, saved, {})
                saved["plan"]["reviewed"] = saved["plan"]["revision"]
                for step in saved["plan"]["spec"]["steps"]:
                    step.pop("operation")
                    step.pop("output_format")
                before = deepcopy(saved)
                await install_plan(service, "alice", sid, Plan.model_validate(saved["plan"]["spec"]), tools,
                    execution, saved, {})
                assert saved == before
                assert not files.requests and not files.writes
        finally:
            await service.close()
    asyncio.run(run())
