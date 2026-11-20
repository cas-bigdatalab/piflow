"""Independent acceptance checks for read-only plan observations and context."""
import asyncio
from copy import deepcopy
import json

from ..dialogue import Dialogue
from ..planning import Workflow, plan_input, plan_view
from ..plan_runtime import compile_workflow
from ..service import DatasetQA
from .assertions import assert_completed
from .test_context_budget import cost, exchange
from .test_dataset_qa import action, collect, engine, load, session
from .test_decisions import BareDialogue, configured, payload, text
from .test_planning import approve
from .test_workflow_input import generic_tools


def test_echoed_plan_observations_cannot_approve_or_create_successful_receipts(engine):
    async def run():
        backend = configured()
        backend.catalog["data"][0].meta["piflow"]["qa"]["plan_required"] = True

        def echo(messages, definitions):
            observed = deepcopy(json.loads(messages[1].content)["plan"])
            observed.update(revision=999, reviewed=True,
                decision={"phase": "execute", "next_action": {"name": "deliver_results"}},
                acceptance={"retrieve": {"state": "accepted"}},
                step_status={"retrieve": "succeeded"})
            observed["editable"]["steps"][0]["state"] = "succeeded"
            return action("remember", plan=observed)

        def review(messages, definitions):
            state = json.loads(messages[1].content)["plan"]
            assert not backend.calls
            assert state["revision"] == 1 and state["reviewed"] is False
            assert state["decision"]["phase"] == "review"
            assert state["step_status"] == {"retrieve": "pending"}
            assert all(item["state"] == "pending" for item in state["acceptance"].values())
            return approve(messages, definitions)

        dialogue = BareDialogue(load(), action("remember", plan={"steps": [
            {"key": "retrieve", "tool": "search", "arguments": {"query": "observations"}}
        ]}), echo, review, text())
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            events = await collect(service, sid, "Find observation records")
            assert_completed(service, sid, events[-1])
            saved = payload(service, sid, events)
            assert saved["plan"]["revision"] == saved["plan"]["reviewed"] == 1
            assert backend.calls == [("data", "search", {"query": "observations"})]
        finally:
            await service.close()
    asyncio.run(run())


def decision_view():
    arguments = {"threshold": 0.8, "lower": -1, "limit": 1000, "strict": False,
        "identifier": "000123", "source": "registry-beta"}
    plan = compile_workflow(Workflow(steps=[
        {"key": "fetch", "tool": "retrieve", "arguments": arguments},
        {"key": "convert", "tool": "transform", "object": "fetch", "arguments": {"format": "csv"}},
    ]), generic_tools())
    from ..operations import Operations
    operations = Operations()
    saved = {"revision": 1, "spec": plan.model_dump(),
        "operations": {"fetch": "op1", "convert": "op2"}}
    return plan_view(saved, operations), arguments


def test_editable_plan_roundtrip_retains_values_types_and_dependency():
    observed, arguments = decision_view()
    before = deepcopy(observed)
    restored = plan_input(observed)
    assert restored.steps[0].arguments == arguments
    assert type(restored.steps[0].arguments["strict"]) is bool
    assert type(restored.steps[0].arguments["limit"]) is int
    assert restored.steps[0].arguments["identifier"] == "000123"
    assert restored.steps[1].arguments == {"format": "csv"}
    assert restored.steps[1].object.model_dump() == {"step": "fetch", "path": "/file"}
    assert observed == before


def test_budget_keeps_current_request_and_pending_plan_decision_with_dependencies():
    observed, _ = decision_view()
    current = "Use registry-beta, threshold 0.8, lower bound -1, 1000 records, CSV."
    required = {"plan": observed, "references": {"current": {
        "result_id": "evidence-beta", "path": "/items/0", "kind": "object"}},
        "memory": {"source_namespace": "registry-beta"}}
    pair = exchange({"saved": True, "plan_decision": observed["decision"]}, name="remember")
    dialogue = Dialogue(model=object())
    minimal = dialogue.messages(current, required)+pair
    large = dialogue.messages(current, {**required, "summary": "Earlier unrelated work. "*3000})+pair
    before = deepcopy(large)
    bounded = dialogue._budget(large, [], len, cost(minimal))
    assert json.loads(bounded[1].content) == required
    assert any(message.type == "human" and message.content == current for message in bounded)
    assert bounded[-2:] == pair
    assert large == before
