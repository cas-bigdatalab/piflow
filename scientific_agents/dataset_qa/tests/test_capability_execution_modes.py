"""Candidate order never selects planning mode for an unrelated operation."""
import asyncio
from itertools import permutations

import pytest

from ..capabilities import TASK
from ..mcp import ToolSession
from ..service import DatasetQA
from .assertions import assert_completed
from .test_dataset_qa import Backend, action, collect, engine, remote, result_cards, session
from .test_decisions import BareDialogue, payload, text
from .test_planning import approve


def mixed_backend(order):
    backend = Backend()
    definitions = {item.name: item for values in backend.catalog.values() for item in values}
    for name in order:
        definitions[name].description = "Available operation"
        definitions[name].meta = {"piflow": {"qa": {
            "atomic": True, "plan_required": name == "multiply",
            "routing": {"group": "calculation" if name == "multiply" else "lookup"}}}}
    backend.catalog = {"shared": [definitions[name] for name in order]}
    return backend


@pytest.fixture
def observed_tools(monkeypatch):
    observed = {}
    prepare, call = ToolSession.prepare, ToolSession.call

    async def capture_prepare(tools, *args, **kwargs):
        await prepare(tools, *args, **kwargs)
        observed["initial_order"] = [tool.name for tool in tools.loaded.values()]
        observed["aliases"] = {tool.name: tool.alias for tool in tools.loaded.values()}

    async def capture_call(tools, *args, **kwargs):
        result = await call(tools, *args, **kwargs)
        observed["after_call_order"] = [tool.name for tool in tools.loaded.values()]
        return result

    monkeypatch.setattr(ToolSession, "prepare", capture_prepare)
    monkeypatch.setattr(ToolSession, "call", capture_call)
    return observed


def assert_initial_actions(definitions, observed):
    names = {item["function"]["name"] for item in definitions}
    assert {name for name in names if name.startswith("mcp_")} == {
        observed["aliases"]["search"], observed["aliases"]["inspect"]}
    remember = next(item["function"] for item in definitions if item["function"]["name"] == "remember")
    assert "plan" in remember["parameters"]["properties"]
    assert "multiply" in remember["description"]


@pytest.mark.parametrize("order", list(permutations(("search", "multiply", "inspect"))))
def test_loaded_order_and_lru_leave_individual_capability_actions_available(engine, observed_tools, order):
    async def run():
        backend = mixed_backend(order)

        def query(messages, definitions):
            assert_initial_actions(definitions, observed_tools)
            return remote("search", query="observations", **{
                TASK: {"complete_request": False}})(messages, definitions)

        def deliver(messages, definitions):
            assert not any(item["function"]["name"].startswith("mcp_") for item in definitions)
            memory = next(item["function"] for item in definitions if item["function"]["name"] == "remember")
            assert set(memory["parameters"]["$defs"]["Goal"]["properties"]["tool"]["enum"]) == set(observed_tools["aliases"].values())
            assert "plan" not in memory["parameters"]["properties"]
            assert len(backend.calls) == 1
            return action("deliver_results")

        dialogue = BareDialogue(query, deliver, text())
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            events = await collect(service, sid, "Find observations")
            assert_completed(service, None, events[-1])
            assert observed_tools["initial_order"] == list(order)
            assert observed_tools["after_call_order"] == [name for name in order if name != "search"] + ["search"]
            assert backend.calls == [("shared", "search", {"query": "observations"})]
            assert len(dialogue.inputs) == 3  # Query, deliver, final; no planning/memory detour.
            assert "plan" not in payload(service, sid, events)
        finally:
            await service.close()
    asyncio.run(run())


def test_unrelated_leading_plan_capability_does_not_force_single_query_to_plan(engine, observed_tools):
    async def run():
        backend = mixed_backend(("multiply", "search", "inspect"))

        def query(messages, definitions):
            assert_initial_actions(definitions, observed_tools)
            return remote("search", query="observations", **{TASK: {"complete_request": True}})(messages, definitions)

        dialogue = BareDialogue(query, text())
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            events = await collect(service, sid, "Find observations")
            assert_completed(service, None, events[-1])
            assert observed_tools["initial_order"][0] == "multiply"
            assert backend.calls == [("shared", "search", {"query": "observations"})]
            assert len(dialogue.inputs) == 2 and dialogue.inputs[-1][1] == []
            saved = payload(service, sid, events)
            assert "plan" not in saved and not saved.get("planning")
            assert [item["state"] for item in saved["operations"]] == ["succeeded"]
        finally:
            await service.close()
    asyncio.run(run())


def test_second_plan_capability_exposes_workflow_without_extra_schema_request(engine, observed_tools):
    async def run():
        backend = mixed_backend(("search", "multiply", "inspect"))

        def plan(messages, definitions):
            assert_initial_actions(definitions, observed_tools)
            assert observed_tools["initial_order"] == ["search", "multiply", "inspect"]
            assert not backend.calls
            return action("remember", plan={
                "outcomes": [{"key": "product", "description": "The requested product", "kind": "multiply"}],
                "steps": [{"key": "calculate", "tool": "multiply", "arguments": {"x": 6, "y": 7},
                    "produces": ["product"]}]})

        dialogue = BareDialogue(plan, approve, text("The product is 42."))
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            events = await collect(service, sid, "Calculate the product of 6 and 7")
            assert_completed(service, None, events[-1])
            assert backend.calls == [("shared", "multiply", {"x": 6, "y": 7})]
            assert len(dialogue.inputs) == 3  # Plan, review, final; no remember(planning=True) round.
            saved = payload(service, sid, events)
            assert saved["plan"]["acceptance"]["product"]["state"] == "accepted"
            assert [item["state"] for item in saved["operations"]] == ["succeeded"]
            assert result_cards(events)[0]["data"] == {"items": [42]}
        finally:
            await service.close()
    asyncio.run(run())
