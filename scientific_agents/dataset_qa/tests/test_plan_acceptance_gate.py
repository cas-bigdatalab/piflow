"""Dependency readiness respects declared hard checks on complete receipts."""
from types import SimpleNamespace

import pytest

from ..execution import Execution
from ..mcp import Tool
from ..operations import Operations
from ..plan_runtime import scheduled_reply
from ..planning import Plan, ResultContract


def scenario(*, field="checks", qualified=False, shared=False, unavailable=False):
    tools = [Tool("source", name, name, {"type": "object", "properties": {}}, {}, {})
        for name in ("fetch", "process", "independent")]
    loaded = SimpleNamespace(loaded={tool.alias: tool for tool in tools})
    outcomes = [{"key": "source", "description": "Qualified source", "kind": "fetch",
        field: [{"path": "/qualified", "test": "equals", "value": True}]},
        {"key": "processed", "description": "Processed source", "kind": "process"},
        {"key": "other", "description": "Independent result", "kind": "independent"}]
    steps = [{"key": "fetch", "tool": "fetch", "produces": ["source"]},
        {"key": "process", "tool": "process", "inputs": {"value": {"step": "fetch", "path": "/value"}},
            "produces": ["processed"]},
        {"key": "independent", "tool": "independent", "produces": ["other"]}]
    mapping = {"fetch": "a", "process": "b", "independent": "c"}
    if shared:
        outcomes.append({"key": "unconstrained", "description": "Same receipt without a quality gate", "kind": "fetch"})
        steps.insert(1, {"key": "shared", "tool": "fetch", "produces": ["unconstrained"]})
        steps[-1]["inputs"] = {"value": {"step": "shared", "path": "/value"}}
        mapping["shared"] = "a"
    plan = Plan(outcomes=outcomes, steps=steps)
    saved = {"spec": plan.model_dump(), "revision": 1, "reviewed": 1, "operations": mapping,
        "contracts": {step.key: ResultContract(kind=step.tool,
            unavailable_when=[{"path": "/available", "test": "equals", "value": False}]
            if unavailable and step.tool == "fetch" else []).model_dump() for step in plan.steps}}
    execution = Execution()
    execution.operations = Operations([
        {"id": "a", "state": "succeeded", "attempts": [{"state": "succeeded", "result_id": "r"}]},
        {"id": "b", "state": "pending", "attempts": []},
        {"id": "c", "state": "pending", "attempts": []}])
    execution.cards["r"] = {"result_id": "r", "data": {"qualified": qualified, "value": 42, "available": not unavailable}}
    return saved, execution, loaded


@pytest.mark.parametrize("shared", [False, True])
def test_failed_hard_check_blocks_only_its_dependants(shared):
    saved, execution, tools = scenario(shared=shared)
    reply, bindings = scheduled_reply(saved, execution, tools, 4)
    assert saved["acceptance"]["source"]["state"] == "incomplete"
    assert set(bindings.values()) == {"c"}
    assert [tools.loaded[call["name"]].name for call in reply.tool_calls] == ["independent"]
    assert execution.operations.get("b")["state"] == "pending"
    assert not execution.operations.get("b")["attempts"]


@pytest.mark.parametrize("field,qualified", [("checks", True), ("targets", False)])
def test_satisfied_hard_checks_and_missed_soft_targets_allow_processing(field, qualified):
    saved, execution, tools = scenario(field=field, qualified=qualified)
    reply, bindings = scheduled_reply(saved, execution, tools, 4)
    assert saved["acceptance"]["source"]["state"] == "accepted"
    assert set(bindings.values()) == {"b", "c"}
    assert next(call for call in reply.tool_calls if bindings[call["id"]] == "b")["args"] == {"value": 42}
    if field == "targets":
        assert saved["acceptance"]["source"]["targets_met"] is False


def test_unavailable_source_still_closes_dependants_without_a_tool_attempt():
    saved, execution, tools = scenario(unavailable=True)
    _, bindings = scheduled_reply(saved, execution, tools, 4)
    assert set(bindings.values()) == {"c"}
    assert execution.operations.get("b")["state"] == "unavailable"
    assert execution.operations.get("b")["unavailable_dependency"] == "a"
    assert not execution.operations.get("b")["attempts"]
