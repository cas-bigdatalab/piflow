"""Dependency status is derived; real attempts and source checks remain authoritative."""
from copy import deepcopy
from types import SimpleNamespace

import pytest

from ..execution import Execution
from ..mcp import Tool
from ..operations import Operations
from ..plan_runtime import scheduled_reply
from ..planning import Plan, ResultContract


def chain():
    plan = Plan.model_validate({"outcomes": [{"key": "result", "description": "Read data", "kind": "records"}],
        "steps": [{"key": "root", "tool": "locate"},
            {"key": "last", "tool": "read", "object": {"step": "middle", "path": ""}, "produces": ["result"]},
            {"key": "middle", "tool": "describe", "object": {"step": "root", "path": ""}}]})
    saved = {"revision": 1, "reviewed": 1, "spec": plan.model_dump(),
        "operations": {step.key: step.key for step in plan.steps},
        "contracts": {step.key: ResultContract(kind="records", requires=[{"path": "/url"}],
            unavailable_when=[{"path": "/available", "test": "equals", "value": False}]).model_dump() for step in plan.steps}}
    execution = Execution()
    execution.operations = Operations([{"id": step.key, "state": "pending", "attempts": []} for step in plan.steps])
    tools = [Tool("data", step.tool, "", {"type": "object", "properties": {}}, {}, {}) for step in plan.steps]
    return saved, execution, SimpleNamespace(loaded={tool.alias: tool for tool in tools})


def finish(execution, key, data):
    rid = key + "-result"
    operation = execution.operations.get(key)
    operation.update(state="succeeded")
    operation["attempts"].append({"state": "succeeded", "result_id": rid})
    execution.cards[key, rid] = {"result_id": rid, "data": data}


@pytest.mark.parametrize("initial", ["failed", "unknown", "unavailable", "unavailable_content"])
def test_recovered_dependency_reopens_unexecuted_chain_without_replaying_receipts(initial):
    saved, execution, tools = chain()
    if initial == "unavailable_content":
        finish(execution, "root", {"available": False})
        # The recovered prerequisite is a separately evidenced replacement step.
        original_root = execution.operations.get("root")
    else:
        execution.operations.get("root").update(state=initial)
    for _ in range(2):
        assert scheduled_reply(saved, execution, tools, 4)[0] is None
        assert execution.operations.get("last")["state"] == "unavailable"
    if initial == "unavailable_content":
        execution.operations.items.append({"id": "replacement", "state": "pending", "attempts": []})
        saved["operations"]["root"] = "replacement"
        finish(execution, "replacement", {"url": "https://example.invalid/current"})
        assert original_root["state"] == "succeeded"
    else:
        finish(execution, "root", {"url": "https://example.invalid/current"})
    receipts = deepcopy(execution.operations.get(saved["operations"]["root"])["attempts"])
    reply, bindings = scheduled_reply(saved, execution, tools, 4)
    assert reply and list(bindings.values()) == ["middle"]
    assert execution.operations.get("last")["state"] == "pending"
    assert execution.operations.get("middle")["target"]["result_id"] == saved["operations"]["root"] + "-result"
    assert "unavailable_dependency" not in execution.operations.get("middle")
    assert execution.operations.get(saved["operations"]["root"])["attempts"] == receipts
    finish(execution, "middle", {"url": "https://example.invalid/ready"})
    reply, bindings = scheduled_reply(saved, execution, tools, 4)
    assert reply and list(bindings.values()) == ["last"]
    finish(execution, "last", {"url": "https://example.invalid/final"})
    assert scheduled_reply(saved, execution, tools, 4)[0] is None
    assert saved["acceptance"]["result"]["state"] == "accepted"


@pytest.mark.parametrize("data", [None, {}, {"available": False}])
def test_recovery_requires_complete_available_source_evidence(data):
    saved, execution, tools = chain()
    root = execution.operations.get("root")
    root["state"] = "failed"
    scheduled_reply(saved, execution, tools, 4)
    if data is None:
        root["state"] = "succeeded"
    else:
        finish(execution, "root", data)
    assert scheduled_reply(saved, execution, tools, 4)[0] is None
    assert not execution.operations.get("middle")["attempts"]


def test_all_dependencies_must_recover_before_a_consumer_runs():
    saved, execution, tools = chain()
    saved["spec"]["steps"].append({"key": "other", "tool": "locate"})
    saved["spec"]["steps"][2]["depends_on"] = ["other"]
    saved["operations"]["other"] = "other"
    saved["contracts"]["other"] = saved["contracts"]["root"]
    execution.operations.items.append({"id": "other", "state": "failed", "attempts": []})
    execution.operations.get("root")["state"] = "failed"
    assert scheduled_reply(saved, execution, tools, 4)[0] is None
    finish(execution, "root", {"url": "https://example.invalid/root"})
    assert scheduled_reply(saved, execution, tools, 4)[0] is None
    assert execution.operations.get("middle")["unavailable_dependency"] == "other"
    finish(execution, "other", {"url": "https://example.invalid/other"})
    reply, bindings = scheduled_reply(saved, execution, tools, 4)
    assert reply and list(bindings.values()) == ["middle"]


@pytest.mark.parametrize("state", ["running", "succeeded", "failed", "unknown", "unavailable"])
def test_dependency_recovery_never_reopens_a_step_with_its_own_attempt(state):
    saved, execution, tools = chain()
    execution.operations.get("root")["state"] = "failed"
    scheduled_reply(saved, execution, tools, 4)
    middle = execution.operations.get("middle")
    middle.update(state=state, attempts=[{"state": state}])
    original = deepcopy(middle)
    finish(execution, "root", {"url": "https://example.invalid/current"})
    assert scheduled_reply(saved, execution, tools, 4)[0] is None
    assert middle == original
