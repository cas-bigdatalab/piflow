"""Accepted state transitions, not memory tool names, establish plan progress."""
import asyncio
from copy import deepcopy
import json

from jsonschema import Draft202012Validator
from langchain_core.messages import ToolMessage
import pytest

from ..contracts import Limits
from ..execution import Execution
from ..service import DatasetQA
from .assertions import assert_completed, assert_handled
from .test_dataset_qa import action, collect, engine, load, result_cards, session
from .test_decisions import BareDialogue, configured, payload, text
from .test_planning import approve


def spec(query="records"):
    return {"steps": [{"key": "retrieve", "tool": "search", "arguments": {"query": query}}]}


def accepted_plan(query="records", revision=1):
    return {"version": 1, "revision": revision,
        "spec": {"outcomes": [{"key": "records", "description": "Find the specified records", "kind": "search"}],
            "steps": [{"key": "retrieve", "tool": "search", "arguments": {"query": query}, "produces": ["records"]}]},
        "operations": {"retrieve": "op1"}}


def remember_observation(execution, runtime, arguments=None):
    return execution.observe("bookkeeping", {"saved": True}, "remember", arguments or {}, {}, runtime=runtime)


def test_first_plan_is_progress_even_when_goal_identity_and_description_are_preserved():
    execution = Execution()
    execution.operations.register("Find the specified records", {"server": "data", "name": "search"}, planned=True)
    runtime = {"planning": True}
    assert remember_observation(execution, runtime)
    old_goals = deepcopy(execution.operations.items)
    runtime["plan"] = accepted_plan()
    assert remember_observation(execution, runtime, {"plan": spec()})
    assert execution.operations.items == old_goals
    assert not remember_observation(execution, deepcopy(runtime), {"plan": spec()})


def test_only_accepted_plan_state_advances_progress_not_raw_bookkeeping_variants():
    execution = Execution()
    runtime = {"planning": True, "plan": accepted_plan()}
    assert remember_observation(execution, runtime, {"plan": spec()})
    assert not remember_observation(execution, runtime, {"plan": spec("unaccepted change")})
    assert not remember_observation(execution, runtime, {"planning": True, "values": {"note": "another spelling"}})
    runtime["plan"] = accepted_plan("refined records", revision=2)
    assert remember_observation(execution, runtime, {"plan": spec("refined records")})
    assert not remember_observation(execution, runtime, {"plan": spec("refined records")})


def test_entering_planning_mode_counts_once_without_manufacturing_goal_or_receipt():
    execution = Execution()
    assert remember_observation(execution, {})
    assert remember_observation(execution, {"planning": True}, {"planning": True})
    assert not remember_observation(execution, {"planning": True}, {"planning": True})
    assert not execution.operations.items and not execution.cards


def prior_native_alias(messages, definitions):
    """A model may recall an old alias although this decision surface hides it."""
    loaded = next(json.loads(message.content) for message in reversed(messages)
        if isinstance(message, ToolMessage) and message.name == "load_mcp_tools")
    alias = next(item["name"] for item in loaded["items"] if item["tool"] == "search")
    assert alias not in {item["function"]["name"] for item in definitions}
    return action(alias, query="records")


def pending_review_schema(messages, definitions):
    state = json.loads(messages[1].content)["plan"]
    assert not state.get("reviewed")
    decision = state["decision"]
    assert decision["phase"] == "review"
    assert decision["next_action"] == {"name": "review_plan", "arguments": {
        "revision": state["revision"], "covered": [item["key"] for item in state["outcomes"]]}}
    response = next(json.loads(message.content) for message in reversed(messages)
        if isinstance(message, ToolMessage) and message.name == "remember")
    assert response["plan_decision"] == decision
    names = {item["function"]["name"] for item in definitions}
    assert "review_plan" in names and not any(name.startswith("mcp_") for name in names)
    remember = next(item["function"] for item in definitions if item["function"]["name"] == "remember")
    schema = remember["parameters"]
    assert set(schema["properties"]) == {"plan"}
    assert not Draft202012Validator(schema).is_valid({"planning": True})
    assert not Draft202012Validator(schema).is_valid({"values": {"note": "execute now"}})
    return schema


@pytest.mark.parametrize("followup", ["same_plan", "memory", "planning"])
def test_goal_plan_repetition_and_repair_reach_dispatch_without_false_stall(engine, followup):
    async def run():
        backend = configured()
        backend.catalog["data"][0].meta["piflow"]["qa"]["plan_required"] = True

        def followup_action(messages, definitions):
            schema = pending_review_schema(messages, definitions)
            arguments = ({"plan": spec()} if followup == "same_plan" else
                {"values": {"note": "ready to retrieve"}} if followup == "memory" else {"planning": True})
            if followup == "same_plan":
                Draft202012Validator(schema).validate(arguments)
            return action("remember", **arguments)

        def review(messages, definitions):
            pending_review_schema(messages, definitions)
            assert not backend.calls
            return approve(messages, definitions)

        dialogue = BareDialogue(action("list_mcp_servers"), load(),
            action("remember", goals=[{"description": "Find the specified records", "tool": "search"}]),
            prior_native_alias, action("remember", plan=spec()), followup_action, review, text())
        limits = Limits(max_stalled_calls=2)
        service = DatasetQA(engine, dialogue, backend.gateway(limits=limits))
        sid = session(service)
        try:
            events = await collect(service, sid, "Find the specified records")
            assert_completed(service, sid, events[-1])
            saved = payload(service, sid, events)
            assert saved["plan"]["revision"] == saved["plan"]["reviewed"] == 1
            assert saved["plan"]["operations"] == {"retrieve": "op1"}
            assert len(saved["operations"]) == 1 and len(result_cards(events)) == 1
            assert backend.calls == [("data", "search", {"query": "records"})]
            assert len(dialogue.inputs) == 8
            assert service.gateway.limits.max_stalled_calls == 2
        finally:
            await service.close()
    asyncio.run(run())


def test_semantic_plan_revision_advances_before_review_without_bookkeeping_loop(engine):
    async def run():
        backend = configured()
        backend.catalog["data"][0].meta["piflow"]["qa"]["plan_required"] = True
        dialogue = BareDialogue(load(),
            action("remember", goals=[{"description": "Find the specified records", "tool": "search"}]),
            action("remember", plan=spec()), action("remember", plan=spec("refined records")),
            action("remember", plan=spec("refined records")), approve, text())
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            events = await collect(service, sid, "Find the specified refined records")
            assert_completed(service, sid, events[-1])
            saved = payload(service, sid, events)
            assert saved["plan"]["revision"] == saved["plan"]["reviewed"] == 2
            assert backend.calls == [("data", "search", {"query": "refined records"})]
            assert len(saved["operations"]) == 1 and len(dialogue.inputs) == 7
        finally:
            await service.close()
    asyncio.run(run())


def test_repeated_identical_plan_remains_bounded_without_business_execution(engine):
    async def run():
        backend = configured()
        backend.catalog["data"][0].meta["piflow"]["qa"]["plan_required"] = True
        dialogue = BareDialogue(load(),
            action("remember", goals=[{"description": "Find the specified records", "tool": "search"}]),
            *[action("remember", plan=spec()) for _ in range(3)])
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            events = await collect(service, sid, "Find the specified records")
            assert_handled(service, sid, events[-1], "no_progress")
            assert not backend.calls and not result_cards(events)
            assert len(dialogue.inputs) == 5
            assert payload(service, sid, events)["plan"]["revision"] == 1
        finally:
            await service.close()
    asyncio.run(run())
