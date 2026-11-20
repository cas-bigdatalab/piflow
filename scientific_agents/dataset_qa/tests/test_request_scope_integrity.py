"""Rejected proposals cannot change focus; adapters own identifier namespaces."""
import asyncio
from copy import deepcopy
import json

from langchain_core.messages import AIMessageChunk
import pytest

from ..capabilities import OBJECT, inputs, profile, same_object_identity
from ..contracts import QAError
from ..execution import Execution
from ..mcp import Tool
from ..service import DatasetQA
from .test_dataset_qa import action, engine, session
from .test_decisions import BareDialogue, configured
from .test_references import stored


def proposal_scope(service, sid, records=None):
    card = stored(service, sid, "source", {"items": records or [
        {"id": "first"}, {"id": "second"}]})
    refs = [{"result_id": card["result_id"], "path": f"/items/{index}", "kind": "object"}
        for index in range(2)]
    context = {"references": {"current": refs[0], "selected": [refs[0]],
        "candidates": {"result_id": card["result_id"], "path": "/items", "kind": "collection"}}}
    payload = {"message": "Show the second object's details and contents", "params": {},
        "parent_task_id": None, "objects": {"object:1": refs[0], "object:2": refs[1]}}
    task, _ = service.store.submit("alice", sid, "proposal", payload, None, service.owner)
    service.store.write("alice", sid, task["id"], context=context, payload=payload)
    return task["id"], payload, context


@pytest.mark.parametrize("invalid", ["goal", "all_native_calls"])
def test_rejected_focus_proposal_is_atomic_in_memory_and_storage(engine, invalid):
    async def run():
        backend = configured()
        service = DatasetQA(engine, BareDialogue(), backend.gateway())
        sid = session(service)
        try:
            tid, payload, context = proposal_scope(service, sid)
            execution = Execution()
            async with service.gateway.session() as tools:
                await tools.load("data")
                loaded, pins = dict(tools.loaded), dict(tools.plan_pins)
                by_name = {tool.name: tool.alias for tool in tools.loaded.values()}
                goals = [{"description": "Requested details", "tool": "unknown-tool" if invalid == "goal"
                    else by_name["inspect"], "object": "object:2"}]
                calls = action("remember", focus="object:2", goals=goals).tool_calls
                if invalid == "all_native_calls":
                    calls += [{"name": by_name[name], "args": {"reference": "conflicting-id",
                        OBJECT: "object:2"}, "id": "invalid-"+name} for name in ("inspect", "preview")]
                before = deepcopy((payload, context, execution.__dict__))
                saved_context = service.store.session("alice", sid)["context"]
                saved_payload = service.store.task("alice", sid, tid)["payload"]
                with pytest.raises(QAError) as error:
                    await service._prepare_operations("alice", sid, tid,
                        AIMessageChunk(content="", tool_calls=calls), tools, execution, payload, context)
                assert error.value.code == "invalid_parameters"
                assert payload == before[0] and context == before[1]
                assert execution.operations.items == before[2]["operations"].items
                assert execution.prepared == before[2]["prepared"]
                assert execution.cards == before[2]["cards"] and execution.blocked == before[2]["blocked"]
                assert tools.loaded == loaded and tools.plan_pins == pins
                assert service.store.session("alice", sid)["context"] == saved_context
                assert service.store.task("alice", sid, tid)["payload"] == saved_payload
                assert not backend.calls
        finally:
            await service.close()
    asyncio.run(run())


def test_valid_goal_without_focus_change_survives_a_correctable_native_argument(engine):
    """Independent goal registration is valid even when its call needs repair."""
    async def run():
        backend = configured()
        service = DatasetQA(engine, BareDialogue(), backend.gateway())
        sid = session(service)
        try:
            tid, payload, context = proposal_scope(service, sid)
            references = deepcopy(context["references"])
            execution = Execution()
            async with service.gateway.session() as tools:
                await tools.load("data")
                alias = next(tool.alias for tool in tools.loaded.values() if tool.name == "inspect")
                calls = action("remember", goals=[{"description": "Requested details", "tool": alias,
                    "object": "object:2"}]).tool_calls
                calls.append({"name": alias, "args": {"reference": "conflicting-id", OBJECT: "object:2"},
                    "id": "correctable-call"})
                await service._prepare_operations("alice", sid, tid,
                    AIMessageChunk(content="", tool_calls=calls), tools, execution, payload, context)
                operation, = execution.operations.required
                assert operation["state"] == "pending" and not operation["attempts"]
                assert operation["target"]["path"] == "/items/1"
                assert execution.prepared["correctable-call"][1].code == "invalid_parameters"
                assert context["references"] == references
                assert not backend.calls
        finally:
            await service.close()
    asyncio.run(run())


def namespaced_tool(**contract):
    return Tool("consumer-service", "inspect", "Inspect an identified record",
        {"type": "object", "properties": {"reference": {"type": "string"}},
            "required": ["reference"], "additionalProperties": False}, {},
        {"piflow": {"qa": {"bind": {"reference": ["/id"]}, **contract}}})


@pytest.mark.parametrize("record,accepted", [
    ({"id": "123", "db": "alpha"}, True),
    ({"id": "123", "db": "beta"}, False),
    ({"id": "123"}, False),
    ({"id": "123", "db": None}, False),
])
def test_declared_input_contract_checks_complete_record_namespace(record, accepted):
    tool = namespaced_tool(input_checks=[{"path": "/db", "test": "equals", "value": "alpha"}])
    original = deepcopy(record)
    if accepted:
        assert inputs(tool, {}, record) == {"reference": "123"}
    else:
        with pytest.raises(QAError) as error:
            inputs(tool, {}, record)
        assert error.value.code == "invalid_parameters"
        assert error.value.detail["origin"] == "object_contract"
    assert record == original


def test_legacy_binding_and_shared_namespaces_do_not_infer_service_restrictions():
    record = {"id": "shared-123", "db": "shared-registry", "server": "producer-service"}
    assert inputs(namespaced_tool(), {}, record) == {"reference": "shared-123"}
    tool = namespaced_tool(input_checks=[{"path": "/db", "test": "equals", "value": "shared-registry"}])
    assert inputs(tool, {}, record) == {"reference": "shared-123"}


@pytest.mark.parametrize("left,right,equivalent", [
    ({"db": "alpha"}, {"db": "alpha"}, True),
    ({"db": "alpha"}, {"db": "beta"}, False),
    ({"db": "alpha"}, {}, False),
    ({}, {}, False),
    ({"db": None}, {"db": None}, False),
    ({"db": 1}, {"db": True}, False),
])
def test_identity_namespace_must_be_present_and_equal(left, right, equivalent):
    tool = namespaced_tool(identity_paths=["/db"])
    assert same_object_identity(tool, {"id": "123", **left}, {"id": "123", **right}) is equivalent


@pytest.mark.parametrize("contract", [
    {"identity_paths": ["db"]},
    {"input_checks": [{"path": "db", "test": "equals", "value": "alpha"}]},
])
def test_invalid_namespace_declarations_are_rejected_at_adapter_validation(contract):
    with pytest.raises(QAError) as error:
        profile(namespaced_tool(**contract))
    assert error.value.code == "invalid_schema"


def test_equal_ids_in_different_namespaces_keep_distinct_outcomes(engine):
    async def run():
        backend = configured()
        backend.catalog["data"][1].meta["piflow"]["qa"]["identity_paths"] = ["/db"]
        service = DatasetQA(engine, BareDialogue(), backend.gateway())
        sid = session(service)
        try:
            tid, payload, context = proposal_scope(service, sid, [
                {"id": "123", "db": "alpha"}, {"id": "123", "db": "beta"}])
            execution = Execution()
            async with service.gateway.session() as tools:
                await tools.load("data")
                alias = next(tool.alias for tool in tools.loaded.values() if tool.name == "inspect")
                reply = action("remember", goals=[
                    {"description": "Inspect alpha", "tool": alias, "object": "object:1"},
                    {"description": "Inspect beta", "tool": alias, "object": "object:2"}])
                await service._prepare_operations("alice", sid, tid, reply, tools, execution, payload, context)
                assert len(execution.operations.required) == 2
                assert [item["target"]["path"] for item in execution.operations.required] == ["/items/0", "/items/1"]
                saved = json.loads(service.store.task("alice", sid, tid)["payload"])
                assert saved["operations"] == execution.operations.items
                assert not backend.calls
        finally:
            await service.close()
    asyncio.run(run())
