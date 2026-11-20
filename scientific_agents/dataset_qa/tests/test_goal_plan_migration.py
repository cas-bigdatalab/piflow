"""Mode changes preserve goal ownership, constraints and exact execution evidence."""
import asyncio
from contextlib import asynccontextmanager
from copy import deepcopy

import pytest

from ..capabilities import resolve_tool
from ..contracts import QAError
from ..execution import Execution, fingerprint
from ..plan_runtime import install_plan, scheduled_reply
from ..planning import Workflow, plan_input, plan_view
from ..service import DatasetQA
from .test_dataset_qa import action, collect, engine, load, session
from .test_decisions import BareDialogue, configured, payload, text
from .test_planning import approve


@asynccontextmanager
async def world(engine):
    backend = configured()
    backend.catalog["data"][0].meta["piflow"]["qa"]["routing"] = {"group": "records", "operations": ["search", "filter"]}
    service = DatasetQA(engine, BareDialogue(), backend.gateway())
    try:
        async with service.gateway.session() as tools:
            await tools.load("data")
            yield service, tools, Execution(), {}, session(service), backend
    finally:
        await service.close()


def goal(execution, tools, description="Retrieve requested records", **kwargs):
    tool = resolve_tool("search", tools.loaded)
    key = execution.operations.register(description, {"server": tool.server, "name": tool.name}, planned=True, **kwargs)
    return execution.operations.get(key)


def workflow(**step):
    return Workflow(steps=[{"key": "find", "tool": "search", "arguments": {"query": "records"}, **step}])


def receipt(item, tools, query="records"):
    tool = resolve_tool("search", tools.loaded)
    item.update(state="succeeded", attempts=[{"key": "recorded", "state": "succeeded", "result_id": "prior:0",
        "invocation": fingerprint([tool.server, tool.name, {"query": query}]), "acceptance": "accepted"}])


@pytest.mark.parametrize("register_first", [False, True])
def test_first_plan_reuses_unexecuted_goal_without_duplicate_work(engine, register_first):
    async def run():
        backend = configured()
        backend.catalog["data"][0].meta["piflow"]["qa"]["plan_required"] = True
        replies = [load()]
        if register_first:
            replies.append(action("remember", goals=[{"description": "Find the specified records", "tool": "search"}]))
        replies.extend([action("remember", plan=workflow().model_dump()), approve, text()])
        dialogue = BareDialogue(*replies)
        service = DatasetQA(engine, dialogue, backend.gateway())
        try:
            sid = session(service)
            events = await collect(service, sid, "Find the specified records")
            saved = payload(service, sid, events)
            assert not saved.get("error")
            assert len(saved["operations"]) == 1
            assert saved["plan"]["operations"] == {"find": "op1"}
            assert saved["plan"]["acceptance"]["find"]["state"] == "accepted"
            assert backend.calls == [("data", "search", {"query": "records"})]
            assert len(dialogue.inputs) == (5 if register_first else 4)
        finally:
            await service.close()
    asyncio.run(run())


def test_ambiguous_goals_require_handles_and_remain_independent(engine):
    async def run():
        async with world(engine) as (service, tools, execution, state, sid, _):
            first = goal(execution, tools, "First independently requested retrieval")
            second = goal(execution, tools, "Second independently requested retrieval")
            before = deepcopy(execution.operations.items)
            with pytest.raises(QAError, match="多个目标") as error:
                await install_plan(service, "alice", sid, workflow(), tools, execution, state, {})
            assert {item["id"] for item in error.value.detail["goals"]} == {first["id"], second["id"]}
            assert execution.operations.items == before and state == {}
            spec = Workflow(steps=[
                {"key": "first", "goal": first["id"], "tool": "search", "arguments": {"query": "records"}},
                {"key": "second", "goal": second["id"], "tool": "search", "arguments": {"query": "records"}}])
            await install_plan(service, "alice", sid, spec, tools, execution, state, {})
            assert state["plan"]["operations"] == {"first": first["id"], "second": second["id"]}
            assert len(execution.operations.items) == 2
            shown = plan_view(state["plan"], execution.operations)
            await install_plan(service, "alice", sid, plan_input(shown), tools, execution, state, {})
            assert state["plan"]["revision"] == 1
    asyncio.run(run())


def test_required_source_remains_an_outcome_when_plan_adds_a_consumer(engine):
    async def run():
        async with world(engine) as (service, tools, execution, state, sid, _):
            item = goal(execution, tools, "Retrieve records under the original conditions", output="answer")
            spec = Workflow(steps=[workflow().steps[0].model_dump(), {"key": "inspect", "tool": "inspect",
                "object": {"step": "find", "path": "/items/0"}}])
            await install_plan(service, "alice", sid, spec, tools, execution, state, {})
            assert {o["key"] for o in state["plan"]["spec"]["outcomes"]} == {"find", "inspect"}
            preserved = execution.operations.get(item["id"])
            assert preserved["output"] == "answer" and preserved["description"] == item["description"]
            assert state["plan"]["operations"]["find"] == item["id"]
    asyncio.run(run())


@pytest.mark.parametrize("mutation", [{"goal": "invented"}, {"deliver": False}, {"operation": "filter"}])
def test_invalid_migration_never_erases_a_declared_goal(engine, mutation):
    async def run():
        async with world(engine) as (service, tools, execution, state, sid, _):
            item = goal(execution, tools)
            item["intent"] = {"operation": "search"}
            before = deepcopy(execution.operations.items)
            # An auxiliary source still has a dependent terminal outcome.
            steps = [workflow(**mutation).steps[0].model_dump(), {"key": "inspect", "tool": "inspect",
                "object": {"step": "find", "path": "/items/0"}}]
            with pytest.raises(QAError):
                await install_plan(service, "alice", sid, Workflow(steps=steps), tools, execution, state, {})
            assert execution.operations.items == before and state == {}
    asyncio.run(run())


@pytest.mark.parametrize("fresh,query,mapped", [(False, "records", True), (True, "records", False), (False, "changed", False)])
def test_completed_goal_reuse_requires_exact_invocation_and_no_fresh_request(engine, fresh, query, mapped):
    async def run():
        async with world(engine) as (service, tools, execution, state, sid, _):
            item = goal(execution, tools)
            receipt(item, tools)
            before = deepcopy(item["attempts"])
            await install_plan(service, "alice", sid, workflow(fresh=fresh, arguments={"query": query}),
                tools, execution, state, {})
            assert (state["plan"]["operations"]["find"] == item["id"]) is mapped
            assert execution.operations.get(item["id"])["attempts"] == before
            assert execution.operations.get(item["id"])["required"]
            assert len(execution.operations.items) == (1 if mapped else 2)
    asyncio.run(run())


@pytest.mark.parametrize("status", ["failed", "unknown", "pending"])
def test_migration_cannot_replay_old_success_over_unfinished_or_unknown_work(engine, status):
    async def run():
        async with world(engine) as (service, tools, execution, state, sid, _):
            item = goal(execution, tools)
            receipt(item, tools)
            item["state"] = status
            before = deepcopy(execution.operations.items)
            with pytest.raises(QAError):
                await install_plan(service, "alice", sid, workflow(goal=item["id"]), tools, execution, state, {})
            assert execution.operations.items == before and state == {}
    asyncio.run(run())


def test_goal_intent_survives_first_plan_and_cannot_be_rewritten(engine):
    async def run():
        async with world(engine) as (service, tools, execution, state, sid, _):
            item = goal(execution, tools)
            item["intent"] = {"operation": "search"}
            await install_plan(service, "alice", sid, workflow(), tools, execution, state, {})
            assert state["plan"]["spec"]["steps"][0]["operation"] == "search"
            assert state["plan"]["spec"]["steps"][0]["goal"] == item["id"]
            with pytest.raises(QAError, match="操作目的"):
                await install_plan(service, "alice", sid, workflow(operation="filter"), tools, execution, state, {})
    asyncio.run(run())


def test_unavailable_prior_goal_does_not_prevent_independent_plan_work(engine):
    async def run():
        async with world(engine) as (service, tools, execution, state, sid, _):
            item = goal(execution, tools)
            item["state"] = "unknown"
            await install_plan(service, "alice", sid, workflow(arguments={"query": "independent request"}),
                tools, execution, state, {})
            assert state["plan"]["operations"]["find"] != item["id"]
            preserved = execution.operations.get(item["id"])
            assert preserved["required"] and preserved["state"] == "unknown"
    asyncio.run(run())


@pytest.mark.parametrize("pointer,expected", [("/items/0", ("page:0", "/items/0", None)),
    ("/items/2", ("page:1", "/items/1", None)), ("/items/2/id", ("page:1", "/items/1/id", "c")),
    ("/total", None), ("/items/9", None)])
def test_search_dependency_uses_deduplicated_row_provenance(engine, pointer, expected):
    async def run():
        async with world(engine) as (service, tools, execution, state, sid, _):
            source = {"step": "find", "path": pointer}
            consumer = {"key": "inspect", "tool": "inspect", **(
                {"inputs": {"reference": source}} if pointer.endswith("/id") else {"object": source})}
            await install_plan(service, "alice", sid, Workflow(steps=[workflow().steps[0].model_dump(), consumer]),
                tools, execution, state, {})
            saved = state["plan"]
            saved["reviewed"] = saved["revision"]
            producer = execution.operations.get(saved["operations"]["find"])
            producer.update(state="succeeded", search={"done": True})
            producer["attempts"] = [{"key": "receipt:" + str(i), "state": "succeeded", "result_id": "page:" + str(i),
                "tool": {"server": "data", "name": "search"}, "retry_safe": True,
                "presentation": {"family": "records", "kind": "collection", "path": "/items", "identity": ["/id"]}}
                for i in range(2)]
            execution.cards = {"page:0": {"result_id": "page:0", "view_type": "table",
                "data": {"items": [{"id": "a"}, {"id": "b"}], "total": 3}},
                "page:1": {"result_id": "page:1", "view_type": "table",
                "data": {"items": [{"id": "a", "extra": "duplicate"}, {"id": "c"}], "total": 3}}}
            reply, bindings = scheduled_reply(saved, execution, tools, 4)
            if expected is None:
                assert reply is None and not bindings and "inspect" in saved["decisions"]
                return
            assert len(reply.tool_calls) == 1
            if expected[2] is not None:
                assert reply.tool_calls[0]["args"] == {"reference": expected[2]}
            else:
                target = execution.operations.get(saved["operations"]["inspect"])["target"]
                assert target == {"result_id": expected[0], "path": expected[1], "kind": "object"}
    asyncio.run(run())
