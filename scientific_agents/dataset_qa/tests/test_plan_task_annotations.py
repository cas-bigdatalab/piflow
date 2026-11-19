"""Known native task annotations compile to Plan intent without losing constraints."""
import asyncio
from copy import deepcopy
import json

import pytest

from mcp_servers.corpus_mcp import mcp
from ..capabilities import TASK
from ..contracts import QAError, Server
from ..execution import Execution
from ..mcp import MCPGateway
from ..plan_runtime import compile_workflow, install_plan
from ..planning import Plan, Workflow
from ..service import DatasetQA
from .test_dataset_qa import action, collect, engine, load, session
from .test_decisions import BareDialogue, configured, payload, text
from .test_file_pipeline import files
from .test_bounded_discovery import KEYWORDS, SearchBackend, page
from .test_planning import approve
from .test_workflow_input import compact_plan, generic_tools


def atomic_tools():
    tools = generic_tools()
    consumer = next(tool for tool in tools.loaded.values() if tool.name == "transform")
    consumer.meta["piflow"]["qa"]["atomic"] = True
    return tools


def annotated_workflow(task):
    return Workflow(steps=[{"key": "fetch", "tool": "retrieve"},
        {"key": "convert", "tool": "transform", "object": "fetch",
            "arguments": {"encoding": "csv", TASK: task}}])


@pytest.mark.parametrize("complete", [False, True])
def test_valid_atomic_annotation_lifts_intent_and_plan_retains_outcome_ownership(complete):
    intent = annotated_workflow({"complete_request": complete, "operation": "export",
        "output_format": "csv", "keywords": None, "original_keywords": None})
    original = intent.model_dump()
    plan = compile_workflow(intent, atomic_tools())
    step = plan.steps[-1]
    assert step.arguments == {"encoding": "csv"}
    assert step.operation == "export" and step.output_format == "csv"
    assert step.produces == ["convert"] and plan.steps[0].produces == []
    assert intent.model_dump() == original


@pytest.mark.parametrize("task", [None, "invalid", {}, {"complete_request": "true"},
    {"complete_request": True, "unknown_control": True},
    {"complete_request": False, "keywords": ["must not disappear"]},
    {"complete_request": False, "original_keywords": ["must not disappear"]}])
def test_invalid_or_search_annotation_is_rejected_with_actionable_plan_location(task):
    with pytest.raises(QAError) as error:
        compile_workflow(annotated_workflow(task), atomic_tools())
    detail = error.value.detail
    assert detail["step"] == "convert" and detail["path"][:2] == ["arguments", TASK]
    assert detail["phase"] == "plan_validation" and detail["dispatched"] is False
    assert "step.operation" in detail["guidance"]


@pytest.mark.parametrize("field,conflict", [("operation", "filter"), ("output_format", "jsonl")])
def test_task_annotation_cannot_replace_explicit_or_inherited_step_intent(field, conflict):
    intent = annotated_workflow({"complete_request": True, "operation": "export", "output_format": "csv"})
    setattr(intent.steps[-1], field, conflict)
    with pytest.raises(QAError) as error:
        compile_workflow(intent, atomic_tools())
    assert error.value.detail["field"] == field
    previous = compile_workflow(annotated_workflow({"complete_request": False,
        "operation": "export", "output_format": "csv"}), atomic_tools())
    changed = annotated_workflow({"complete_request": True, field: conflict})
    with pytest.raises(QAError):
        compile_workflow(changed, atomic_tools(), {"spec": previous.model_dump()})


@pytest.mark.parametrize("strict", [False, True])
def test_atomic_annotations_execute_query_export_once_in_workflow_and_strict_plan(engine, files, strict):
    async def run():
        intent = compact_plan()
        intent["steps"][0]["arguments"][TASK] = {"complete_request": True}
        intent["steps"][-1]["arguments"][TASK] = {
            "complete_request": True, "operation": "export", "output_format": "csv"}
        if strict:
            intent["outcomes"] = [{"key": "csv", "description": "Requested CSV", "kind": "exported_file"}]
            intent["steps"][-1]["produces"] = ["csv"]
            intent["steps"][-1]["object"] = {"step": "query", "path": "/resource"}
        service = DatasetQA(engine, BareDialogue(action("remember", plan=intent), approve, text()),
            MCPGateway({"piflow-corpus": Server(mcp)}))
        try:
            sid = session(service)
            events = await collect(service, sid, "Find PubChem compounds and save the requested CSV")
            saved = payload(service, sid, events)
            assert not saved.get("error")
            assert len(files.requests) == 2  # One similarity search and one property retrieval.
            assert len(saved["operations"]) == 2 and all(len(op["attempts"]) == 1 for op in saved["operations"])
            steps = saved["plan"]["spec"]["steps"]
            assert all(TASK not in step["arguments"] for step in steps)
            assert steps[-1]["operation"] == "export" and steps[-1]["output_format"] == "csv"
            assert all(item["state"] == "accepted" for item in saved["plan"]["acceptance"].values())
        finally:
            await service.close()
    asyncio.run(run())


def test_lifted_intent_does_not_change_conflicting_business_format(engine, files):
    async def run():
        service = DatasetQA(engine, BareDialogue(), MCPGateway({"piflow-corpus": Server(mcp)}))
        try:
            async with service.gateway.session() as tools:
                await tools.load("piflow-corpus", query="PubChem CSV")
                intent = compact_plan()
                intent["steps"][-1]["arguments"].update(format="jsonl", **{TASK: {
                    "complete_request": True, "operation": "export", "output_format": "csv"}})
                state, execution = {}, Execution()
                with pytest.raises(QAError) as error:
                    await install_plan(service, "alice", session(service), Workflow.model_validate(intent),
                        tools, execution, state, {})
                assert error.value.detail["phase"] == "plan_validation"
                assert not state and not execution.operations.items and not files.requests
                assert intent["steps"][-1]["arguments"]["format"] == "jsonl"
        finally:
            await service.close()
    asyncio.run(run())


@pytest.mark.parametrize("task", [{"complete_request": False},
    {"complete_request": False, "operation": "export", "output_format": "csv"}])
def test_legacy_saved_atomic_annotation_remains_idempotent(engine, files, task):
    async def run():
        service = DatasetQA(engine, BareDialogue(), MCPGateway({"piflow-corpus": Server(mcp)}))
        try:
            async with service.gateway.session() as tools:
                await tools.load("piflow-corpus", query="PubChem CSV")
                state, execution = {}, Execution()
                sid = session(service)
                await install_plan(service, "alice", sid, Workflow.model_validate(compact_plan()), tools, execution, state, {})
                state["plan"]["spec"]["steps"][-1]["arguments"][TASK] = task
                state["plan"]["reviewed"] = state["plan"]["revision"]
                previous = deepcopy(state)
                await install_plan(service, "alice", sid, Plan.model_validate(state["plan"]["spec"]), tools, execution, state, {})
                assert state == previous and not files.requests
        finally:
            await service.close()
    asyncio.run(run())


def test_search_keyword_directives_are_not_removed_by_atomic_annotation_lifting():
    tools = atomic_tools()
    consumer = next(tool for tool in tools.loaded.values() if tool.name == "transform")
    consumer.schema["properties"]["phrase"] = {"type": "string"}
    consumer.meta["piflow"]["qa"].update(collection="/items", search={"query": "phrase"})
    task = {"complete_request": False, "keywords": KEYWORDS, "original_keywords": KEYWORDS[:1]}
    intent = annotated_workflow(task)
    intent.steps[-1].arguments["phrase"] = KEYWORDS[0]
    assert compile_workflow(intent, tools).steps[-1].arguments[TASK] == task


def test_legacy_invalid_atomic_annotation_can_be_repaired_without_replaying_completed_source(engine, files, monkeypatch):
    from .. import service as service_module
    original_install = service_module.install_plan
    seeded = False

    async def legacy_install(*args, **kwargs):
        nonlocal seeded
        await original_install(*args, **kwargs)
        if not seeded:
            seeded = True
            steps = args[6]["plan"]["spec"]["steps"]
            steps[0]["arguments"][TASK] = {"complete_request": False}
            steps[-1]["arguments"][TASK] = {"complete_request": False, "unknown_control": True}

    monkeypatch.setattr(service_module, "install_plan", legacy_install)

    def repair(messages, definitions):
        assert len(files.requests) == 2
        view = json.loads(messages[1].content)["plan"]
        fixed = deepcopy(view["editable"])
        for step in fixed["steps"]:
            step["arguments"].pop(TASK, None)
        return action("remember", plan=fixed)

    async def run():
        service = DatasetQA(engine, BareDialogue(action("remember", plan=compact_plan()), approve,
            repair, approve, text()), MCPGateway({"piflow-corpus": Server(mcp)}))
        try:
            sid = session(service)
            events = await collect(service, sid, "Find PubChem compounds and save as CSV")
            saved = payload(service, sid, events)
            assert not saved.get("error") and saved["plan"]["revision"] == 2
            assert len(files.requests) == 2
            assert len(saved["operations"][0]["attempts"]) == 1
            assert [attempt["state"] for attempt in saved["operations"][-1]["attempts"]] == ["rejected", "succeeded"]
            assert all(TASK not in step["arguments"] for step in saved["plan"]["spec"]["steps"])
        finally:
            await service.close()
    asyncio.run(run())


def test_search_whole_request_annotation_is_rejected_with_precise_location(engine):
    async def run():
        backend = SearchBackend(lambda word, number: page([1], 1))
        service = DatasetQA(engine, BareDialogue(), backend.gateway())
        try:
            async with service.gateway.session() as tools:
                await tools.load("arbitrary-source")
                intent = Workflow(steps=[{"key": "find", "tool": "find_assets", "arguments": {
                    "phrase": KEYWORDS[0], TASK: {"complete_request": True,
                        "keywords": KEYWORDS, "original_keywords": KEYWORDS[:1]}}}])
                state, execution = {}, Execution()
                with pytest.raises(QAError) as error:
                    await install_plan(service, "alice", session(service), intent, tools, execution, state, {})
                assert error.value.detail["path"] == ["arguments", TASK, "complete_request"]
                assert "complete_request=false" in error.value.detail["guidance"]
                assert not state and not execution.operations.items and not backend.calls
        finally:
            await service.close()
    asyncio.run(run())


def test_native_reserved_name_is_preserved_as_business_data(engine):
    async def run():
        backend = configured()
        tool = backend.catalog["data"][1]
        tool.meta = {"piflow": {"qa": {"atomic": True}}}
        tool.inputSchema["properties"][TASK] = {"type": "object"}
        arguments = {"reference": "native-value", TASK: {"complete_request": True, "business_payload": [1, False]}}
        service = DatasetQA(engine, BareDialogue(load(), action("remember", plan={"steps": [
            {"key": "native", "tool": "inspect", "arguments": arguments}]}), approve, text()), backend.gateway())
        try:
            sid = session(service)
            events = await collect(service, sid, "Inspect the requested native record")
            assert not payload(service, sid, events).get("error")
            assert backend.calls == [("data", "inspect", arguments)]
        finally:
            await service.close()
    asyncio.run(run())
