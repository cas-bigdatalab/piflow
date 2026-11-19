"""Accepted plans retain their bounded, validated tool working set."""
import asyncio
from copy import deepcopy
from dataclasses import replace
import json

import pytest

from ..context import encode
from ..contracts import Limits, QAError
from ..execution import Execution
from ..operations import Operations
from ..plan_runtime import confirm_plan, install_plan, scheduled_reply
from ..planning import Review, Workflow
from ..service import DatasetQA
from .test_dataset_qa import action, collect, engine, load, session
from .test_decisions import BareDialogue, configured, payload, text
from .test_plan_recovery import workflow
from .test_planning import approve


async def install(service, tools, state=None, execution=None, plan=None):
    state = state if state is not None else {}
    execution = execution or Execution()
    await install_plan(service, "alice", session(service), Workflow.model_validate(plan or workflow()),
        tools, execution, state, {})
    return state, execution


@pytest.mark.parametrize("budget", ["tools", "schema"])
def test_discovery_cannot_evict_an_accepted_plan_before_scheduler_runs(engine, budget):
    async def run():
        backend = configured()
        limits = Limits(max_tools=2)
        if budget == "schema":
            async with backend.gateway().session() as tools:
                await tools.load("data", query="search inspect", limit=2)
                limits = replace(Limits(), schema_chars=len(encode(tools.definitions())))
        dialogue = BareDialogue(load(query="search inspect", limit=2),
            action("remember", plan=workflow()), load("compute"), approve, text())
        service = DatasetQA(engine, dialogue, backend.gateway(limits=limits))
        try:
            sid = session(service)
            events = await collect(service, sid, "find and inspect the first resource")
            saved = payload(service, sid, events)
            assert not saved.get("error")
            assert [name for _, name, _ in backend.calls] == ["search", "inspect"]
            feedback = [json.loads(message.content) for messages, _ in dialogue.inputs
                for message in messages if message.type == "tool"]
            blocked = next(value for value in feedback if value.get("protected_tools"))
            assert blocked["not_loaded"][0]["error"] == ("tool_budget" if budget == "tools" else "schema_budget")
            assert len(saved["plan"]["tool_definitions"]) == 2
            assert len(dialogue.inputs) == 5  # No model correction or repeated prerequisite.
        finally:
            await service.close()
    asyncio.run(run())


def test_pinned_definition_survives_discovery_refresh_and_is_task_local(engine):
    async def run():
        backend = configured()
        gateway = backend.gateway(limits=Limits(max_tools=2, cache_seconds=0))
        service = DatasetQA(engine, BareDialogue(), gateway)
        try:
            async with gateway.session() as tools:
                await tools.load("data", query="search inspect", limit=2)
                await install(service, tools)
                search = next(tool for tool in tools.loaded.values() if tool.name == "search")
                original = deepcopy(search.schema)
                backend.catalog["data"][0].inputSchema["properties"]["query"]["type"] = "integer"
                await tools.load("data", query="search", limit=1)
                assert tools.loaded[search.alias].schema == original
                assert tools.validate(search.alias, {"query": "resources"})
                # Mutable loaded views cannot alter the pinned contract either.
                tools.loaded[search.alias].schema["properties"]["query"]["type"] = "integer"
                assert tools.validate(search.alias, {"query": "resources"})
            async with gateway.session() as tools:
                assert not tools.plan_pins
                await tools.load("data", query="search", limit=1)
                with pytest.raises(QAError):
                    tools.validate(search.alias, {"query": "resources"})
                await tools.load("compute")
                assert any(tool.name == "multiply" for tool in tools.loaded.values())
        finally:
            await service.close()
    asyncio.run(run())


def test_plan_revision_updates_protection_only_after_success(engine):
    async def run():
        backend = configured()
        service = DatasetQA(engine, BareDialogue(), backend.gateway(limits=Limits(max_tools=3)))
        try:
            async with service.gateway.session() as tools:
                await tools.load("data", query="search inspect", limit=2)
                state, execution = await install(service, tools)
                before, pins = deepcopy(state), deepcopy(tools.plan_pins)
                invalid = workflow()
                invalid["steps"][0]["arguments"]["query"] = 123
                with pytest.raises(QAError):
                    await install(service, tools, state, execution, invalid)
                assert state == before and tools.plan_pins == pins
                # Replacing an unexecuted prerequisite is allowed; the requested
                # detail outcome stays unchanged and receives an explicit ID.
                revised = {"steps": [{"key": "detail", "tool": "inspect", "arguments": {"reference": "a"}}]}
                state["message"] = "inspect a"
                await install(service, tools, state, execution, revised)
                assert {tool.name for tool in tools.plan_pins.values()} == {"inspect"}
                revision = state["plan"]["revision"]
                await install(service, tools, state, execution, revised)
                assert state["plan"]["revision"] == revision
                await tools.load("compute")
                await tools.load("data", query="preview", limit=1)
                assert {tool.name for tool in tools.loaded.values()} == {"inspect", "multiply", "preview"}
        finally:
            await service.close()
    asyncio.run(run())


def test_restored_plan_keeps_successful_receipts_and_schedules_only_pending_step(engine):
    async def run():
        backend = configured()
        service = DatasetQA(engine, BareDialogue(), backend.gateway(limits=Limits(max_tools=2)))
        try:
            async with service.gateway.session() as tools:
                await tools.load("data", query="search inspect", limit=2)
                state, execution = await install(service, tools)
                confirm_plan(state, Review(revision=1, covered=["detail"]))
                reply, bindings = scheduled_reply(state["plan"], execution, tools, 1)
                call = reply.tool_calls[0]
                tool, output = await tools.call(call["name"], call["args"])
                operation_id = bindings[call["id"]]
                execution.operations.start(operation_id, "first", {"server": tool.server, "name": tool.name},
                    False, "first-invocation")
                execution.operations.finish(operation_id, "first", result_id="first-result")
                execution.cards[("first", "test")] = {"result_id": "first-result", **output.payload()}
                saved = json.loads(encode(state["plan"]))
                receipts = deepcopy(execution.operations.items)
            # A fresh gateway models process restart, without reusing discovery.
            restarted = backend.gateway(limits=Limits(max_tools=2))
            async with restarted.session() as tools:
                await tools.load("compute")
                await tools.restore_plan(saved)
                assert {tool.name for tool in tools.loaded.values()} == {"search", "inspect"}
                execution.operations = Operations(receipts)
                reply, bindings = scheduled_reply(saved, execution, tools, 1)
                assert len(reply.tool_calls) == 1
                assert tools.loaded[reply.tool_calls[0]["name"]].name == "inspect"
                assert execution.operations.items[0] == receipts[0]
                assert not execution.operations.items[1]["attempts"]
                assert execution.operations.items[1]["target"]["result_id"] == "first-result"
                assert [name for _, name, _ in backend.calls] == ["search"]
                await tools.load("compute")
                assert {tool.name for tool in tools.loaded.values()} == {"search", "inspect"}
        finally:
            await service.close()
    asyncio.run(run())


@pytest.mark.parametrize("drift", ["schema", "binding", "execution_hint", "missing"])
def test_restore_rejects_changed_definitions_atomically_without_execution(engine, drift):
    async def run():
        backend = configured()
        service = DatasetQA(engine, BareDialogue(), backend.gateway())
        try:
            async with service.gateway.session() as tools:
                await tools.load("data", query="search inspect", limit=2)
                state, _ = await install(service, tools)
                saved = deepcopy(state["plan"])
            if drift == "schema":
                backend.catalog["data"][1].inputSchema["properties"]["reference"]["minLength"] = 2
            elif drift == "binding":
                backend.catalog["data"][1].meta["piflow"]["qa"]["bind"] = {"reference": ["/other"]}
            elif drift == "execution_hint":
                backend.catalog["data"][1].annotations["readOnlyHint"] = True
            else:
                backend.catalog["data"].pop(1)
            async with backend.gateway().session() as tools:
                await tools.load("compute")
                before = deepcopy(tools.loaded)
                with pytest.raises(QAError) as error:
                    await tools.restore_plan(saved)
                assert error.value.detail["phase"] == "plan_restore"
                assert error.value.detail["dispatched"] is False
                assert tools.loaded == before and not tools.plan_pins
                assert not backend.calls
        finally:
            await service.close()
    asyncio.run(run())


def test_restore_accepts_display_metadata_changes(engine):
    async def run():
        backend = configured()
        service = DatasetQA(engine, BareDialogue(), backend.gateway())
        try:
            async with service.gateway.session() as tools:
                await tools.load("data", query="search inspect", limit=2)
                state, _ = await install(service, tools)
                saved = deepcopy(state["plan"])
            changed = backend.catalog["data"][1]
            changed.description = "Updated display explanation"
            changed.annotations["title"] = "Updated title"
            changed.meta.update(updated_at="2030-01-01")
            changed.meta["piflow"].update(icon="new-icon", displayName="New display name", version="2")
            changed.meta["piflow"]["qa"].update(label="New label", name_paths=["/title"])
            async with backend.gateway().session() as tools:
                await tools.restore_plan(saved)
                restored = next(tool for tool in tools.loaded.values() if tool.name == "inspect")
                assert restored.title == "Updated title"
                assert restored.description == "Updated display explanation"
                assert {tool.name for tool in tools.plan_pins.values()} == {"search", "inspect"}
                assert not backend.calls
        finally:
            await service.close()
    asyncio.run(run())


@pytest.mark.parametrize("reviewed", [False, True])
def test_rejected_inherited_plan_revision_can_switch_to_new_without_old_pins(engine, monkeypatch, reviewed):
    from ..mcp import ToolSession
    from .assertions import assert_completed
    from .test_continuation_atomicity import relation
    from .test_dataset_qa import remote

    async def run():
        backend = configured()
        waiting_plan = workflow()
        if reviewed:
            waiting_plan["steps"][1]["object"]["path"] = "/items/99"
        dialogue = BareDialogue(load(query="search inspect", limit=2),
            action("remember", plan=waiting_plan), *([approve] if reviewed else []),
            action("request_input", missing="目标条目", question="需要查看哪条候选记录？"))
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        observed_pins = []
        original_call = ToolSession.call

        async def capture(tools, alias, arguments, **kwargs):
            if arguments.get("query") == "new subject":
                observed_pins.append(set(tools.plan_pins))
            return await original_call(tools, alias, arguments, **kwargs)

        monkeypatch.setattr(ToolSession, "call", capture)
        try:
            waiting = await collect(service, sid, "find and inspect a resource", "waiting-plan")
            assert waiting[-1]["status"] == "WAITING_INPUT"
            original = deepcopy(payload(service, sid, waiting))
            assert original["plan"]["tool_definitions"]
            assert (original["plan"].get("reviewed") == original["plan"]["revision"]) is reviewed
            previous_calls = deepcopy(backend.calls)
            assert len(previous_calls) == int(reviewed)

            invalid = workflow()
            invalid["steps"][0]["arguments"]["query"] = 123
            dialogue.responses = [action("remember", continuation="continue", plan=invalid),
                relation("new", remote("search", query="new subject")),
                action("deliver_results"), text()]
            events = await collect(service, sid, "instead find datasets about a new subject", "new-subject")

            assert_completed(service, None, events[-1])
            saved = payload(service, sid, events)
            assert saved["resume"] is False and "plan" not in saved
            assert observed_pins == [set()]
            assert backend.calls == [*previous_calls, ("data", "search", {"query": "new subject"})]
            assert len(saved["operations"]) == 1
            assert saved["operations"][0]["capability"]["name"] == "search"
            assert payload(service, sid, waiting) == original
        finally:
            await service.close()
    asyncio.run(run())
