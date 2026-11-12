"""Model expression and dispatch recovery regressions, independent of a data source."""
import asyncio
from copy import deepcopy
import json

import pytest

from mcp_servers.corpus_mcp import mcp

from ..contracts import QAError, Server
from ..mcp import MCPGateway
from ..planning import Workflow
from ..plan_runtime import compile_workflow, install_plan
from ..execution import Execution
from ..service import DatasetQA
from .test_dataset_qa import action, collect, engine, load, remote, result_cards, session
from .test_decisions import BareDialogue, configured, payload, text
from .test_planning import approve
from .test_workflow_input import generic_tools
from .test_workflow_input import compact_plan
from .test_file_pipeline import files
from .test_local_artifacts import download_client


def workflow(reference=None):
    result = {"steps": [
        {"key": "find", "tool": "search", "arguments": {"query": "resources"}},
        {"key": "detail", "tool": "inspect", "object": {"step": "find", "path": "/items/0"}}]}
    if reference is not None:
        result["steps"][1]["arguments"] = {"reference": reference}
    return result


@pytest.mark.parametrize("value", [None, {"step": "find", "path": "/items/0/id"}])
def test_source_placeholders_and_inline_refs_resolve_to_real_values(engine, value):
    async def run():
        backend = configured()
        plan = workflow()
        plan["steps"][1]["arguments"] = {"reference": value}
        dialogue = BareDialogue(load(), action("remember", plan=plan), approve, text())
        service = DatasetQA(engine, dialogue, backend.gateway())
        try:
            sid = session(service)
            events = await collect(service, sid, "find and inspect the first resource")
            assert not payload(service, sid, events).get("error")
            assert [name for _, name, _ in backend.calls] == ["search", "inspect"]
            assert backend.calls[-1][2] == {"reference": "a"}
            assert len(dialogue.inputs) == 4
        finally:
            await service.close()
    asyncio.run(run())


@pytest.mark.parametrize("second_rejection", [False, True])
def test_local_rejection_returns_to_model_and_preserves_completed_prerequisite(engine, second_rejection):
    async def run():
        backend = configured()
        repairs = []
        def repair(messages, definitions):
            # Before the fix the scheduler retried three times without reaching here.
            state = json.loads(messages[1].content)
            assert [name for _, name, _ in backend.calls] == ["search"]
            assert not any(d["function"]["name"].startswith("mcp_") for d in definitions)
            feedback = [json.loads(m.content) for m in messages if m.type == "tool"][-1]
            assert feedback["detail"]["dispatched"] is False
            assert feedback["detail"]["step"] == "detail"
            assert "expected" not in feedback["detail"]  # No copied opaque source token.
            repairs.append(state["plan"]["revision"])
            return action("remember", plan=workflow("still-wrong" if second_rejection and len(repairs) == 1 else None))
        responses = [load(), action("remember", plan=workflow("wrong-source")), approve, repair, approve]
        if second_rejection:
            responses.extend([repair, approve])
        dialogue = BareDialogue(*responses, text())
        service = DatasetQA(engine, dialogue, backend.gateway())
        try:
            sid = session(service)
            events = await collect(service, sid, "find and inspect the first resource")
            saved = payload(service, sid, events)
            assert not saved.get("error")
            assert repairs == ([1, 2] if second_rejection else [1])
            assert [name for _, name, _ in backend.calls] == ["search", "inspect"]
            assert backend.calls[-1][2] == {"reference": "a"}
            attempts = saved["operations"][1]["attempts"]
            assert [a["state"] for a in attempts] == ["rejected"] * len(repairs) + ["succeeded"]
            assert all(a["dispatched"] is False for a in attempts[:-1])
            assert len(saved["operations"][0]["attempts"]) == 1
        finally:
            await service.close()
    asyncio.run(run())


def test_unchanged_plan_does_not_authorize_another_rejected_dispatch(engine):
    async def run():
        backend = configured()
        def unchanged(messages, definitions):
            return action("remember", plan=workflow("wrong-source"))
        dialogue = BareDialogue(load(), action("remember", plan=workflow("wrong-source")), approve,
            unchanged, unchanged, text())
        service = DatasetQA(engine, dialogue, backend.gateway())
        try:
            sid = session(service)
            events = await collect(service, sid, "find and inspect the first resource")
            saved = payload(service, sid, events)
            assert [name for _, name, _ in backend.calls] == ["search"]
            assert len(saved["operations"][1]["attempts"]) == 1
            assert saved["plan"]["revision"] == 1
        finally:
            await service.close()
    asyncio.run(run())


def test_nullable_values_and_valid_business_objects_remain_literals():
    tools = generic_tools()
    consumer = next(t for t in tools.loaded.values() if t.name == "transform")
    consumer.schema["properties"]["source"] = {"type": ["string", "null", "object"]}
    for literal in (None, {"step": "fetch", "path": "/file"}):
        plan = compile_workflow(Workflow(steps=[{"key": "fetch", "tool": "retrieve"},
            {"key": "convert", "tool": "transform", "arguments": {"source": literal}}]), tools)
        assert plan.steps[-1].arguments == {"source": literal}
        assert not plan.steps[-1].inputs and plan.steps[-1].object is None


def test_nonnullable_null_uses_only_unambiguous_declared_file_source():
    steps = [{"key": "fetch", "tool": "retrieve"},
        {"key": "convert", "tool": "transform", "arguments": {"source": None}}]
    original = deepcopy(steps)
    plan = compile_workflow(Workflow(steps=steps), generic_tools())
    assert plan.steps[-1].arguments == {}
    assert plan.steps[-1].object.step == "fetch"
    assert steps == original
    steps.insert(1, {"key": "another", "tool": "retrieve"})
    with pytest.raises(QAError, match="多个可用来源"):
        compile_workflow(Workflow(steps=steps), generic_tools())


def test_missing_source_with_null_is_rejected_before_any_execution(engine):
    async def run():
        backend = configured()
        service = DatasetQA(engine, BareDialogue(), backend.gateway())
        try:
            async with service.gateway.session() as tools:
                await tools.load("data")
                plan = Workflow(steps=[{"key": "inspect", "tool": "inspect", "arguments": {"reference": None}}])
                state, execution = {}, Execution()
                with pytest.raises(QAError) as error:
                    await install_plan(service, "alice", session(service), plan, tools, execution, state, {})
                assert error.value.detail["actual_type"] == "null"
                assert error.value.detail["step"] == "inspect"
                assert error.value.detail["dispatched"] is False
                assert not backend.calls and not state and not execution.operations.items
        finally:
            await service.close()
    asyncio.run(run())


def test_resolved_input_type_error_can_be_repaired_without_repeating_query(engine):
    async def run():
        backend = configured()
        plan = workflow()
        consumer = plan["steps"][-1]
        consumer.pop("object")
        consumer["inputs"] = {"reference": {"step": "find", "path": "/items/0"}}
        def repair(messages, definitions):
            assert [name for _, name, _ in backend.calls] == ["search"]
            feedback = [json.loads(m.content) for m in messages if m.type == "tool"][-1]
            assert feedback["detail"]["actual_type"] == "object"
            assert feedback["detail"]["dispatched"] is False
            assert set(feedback["available_actions"]) <= {d["function"]["name"] for d in definitions}
            fixed = deepcopy(plan)
            fixed["steps"][-1]["inputs"]["reference"]["path"] += "/id"
            return action("remember", plan=fixed)
        dialogue = BareDialogue(load(), action("remember", plan=plan), approve, repair, approve, text())
        service = DatasetQA(engine, dialogue, backend.gateway())
        try:
            sid = session(service)
            events = await collect(service, sid, "find and inspect")
            saved = payload(service, sid, events)
            assert not saved.get("error")
            assert [name for _, name, _ in backend.calls] == ["search", "inspect"]
            assert backend.calls[-1][2] == {"reference": "a"}
            assert [a["state"] for a in saved["operations"][-1]["attempts"]] == ["rejected", "succeeded"]
        finally:
            await service.close()
    asyncio.run(run())


def test_local_rejection_does_not_cancel_independent_ready_work(engine):
    async def run():
        backend = configured()
        plan = workflow("wrong-source")
        plan["steps"].append({"key": "sample", "tool": "sample", "arguments": {"count": 3},
            "object": {"step": "find", "path": "/items/1"}})
        def repair(messages, definitions):
            assert [name for _, name, _ in backend.calls] == ["search", "sample"]
            fixed = deepcopy(plan)
            fixed["steps"][1].pop("arguments")
            return action("remember", plan=fixed)
        service = DatasetQA(engine, BareDialogue(load(), action("remember", plan=plan), approve, repair, approve, text()), backend.gateway())
        try:
            sid = session(service)
            events = await collect(service, sid, "inspect the first result and sample the second")
            assert not payload(service, sid, events).get("error")
            assert [name for _, name, _ in backend.calls] == ["search", "sample", "inspect"]
        finally:
            await service.close()
    asyncio.run(run())


def test_planning_catalogue_is_the_only_business_entry_when_planning(engine):
    async def run():
        backend = configured()
        backend.catalog["data"][0].meta["piflow"]["qa"]["plan_required"] = True
        def understand(messages, definitions):
            assert not any(d["function"]["name"].startswith("mcp_") for d in definitions)
            entry = next(d["function"] for d in definitions if d["function"]["name"] == "remember")
            catalog = json.loads(entry["description"].split("Catalogue: ", 1)[1])
            assert {row["tool"].rsplit("_", 1)[-1] for row in catalog} == {"search", "inspect", "sample", "preview"}
            assert next(row for row in catalog if row["tool"].endswith("_inspect"))["object_bindings"] == {"reference": ["/id", "/reference"]}
            return action("remember", plan=workflow())
        dialogue = BareDialogue(load(query="search"), understand, approve, text())
        service = DatasetQA(engine, dialogue, backend.gateway())
        try:
            sid = session(service)
            events = await collect(service, sid, "find and inspect the first resource")
            assert not payload(service, sid, events).get("error")
        finally:
            await service.close()
    asyncio.run(run())


@pytest.mark.parametrize("binding", ["object_null", "inline", "inputs"])
def test_file_pipeline_binds_real_opaque_source_without_model_copying(engine, files, download_client, binding):
    async def run():
        plan = compact_plan()
        export = plan["steps"][-1]
        if binding == "object_null":
            export["arguments"]["source_ref"] = None
        else:
            export.pop("object")
            pointer = {"step": "query", "path": "/resource/source_ref"}
            if binding == "inline":
                export["arguments"]["source_ref"] = pointer
            else:
                export["inputs"] = {"source_ref": pointer}
        service = DatasetQA(engine, BareDialogue(action("remember", plan=plan), approve, text()),
            MCPGateway({"piflow-corpus": Server(mcp)}))
        try:
            sid = session(service)
            events = await collect(service, sid, "PubChem compounds as CSV")
            saved = payload(service, sid, events)
            assert not saved.get("error")
            assert saved["plan"]["acceptance"]["export"]["state"] == "accepted"
            assert all(len(op["attempts"]) == 1 for op in saved["operations"])
            result = result_cards(events)[0]["data"]["items"][0]
            assert result["resource"]["format"] == "csv"
            assert download_client.get(result["downloadUrl"]).status_code == 200
        finally:
            await service.close()
    asyncio.run(run())


def test_finished_plan_does_not_force_next_turn_into_planning(engine):
    async def run():
        backend = configured()
        service = DatasetQA(engine, BareDialogue(load(), action("remember", plan=workflow()), approve, text()), backend.gateway())
        try:
            sid = session(service)
            first = await collect(service, sid, "find and inspect the first resource", rid="plan")
            assert not payload(service, sid, first).get("error")
            service.dialogue = BareDialogue(remote("inspect", __qa_object="current"), action("deliver_results"), text())
            second = await collect(service, sid, "inspect this resource again", rid="react")
            saved = payload(service, sid, second)
            assert not saved.get("error") and not saved.get("plan")
            assert len(service.dialogue.inputs) == 3
            assert [name for _, name, _ in backend.calls] == ["search", "inspect", "inspect"]
            assert backend.calls[-1][2] == {"reference": "a"}
        finally:
            await service.close()
    asyncio.run(run())
