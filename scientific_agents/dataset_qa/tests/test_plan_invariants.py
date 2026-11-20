"""Counterexamples from a logical audit, not just the expected workflow path."""
import asyncio
from copy import deepcopy

import pytest

from ..contracts import QAError
from ..execution import Execution
from ..operations import Operations
from ..planning import Plan, Workflow, plan_input, plan_view, validate_revision
from ..plan_runtime import compile_workflow, install_plan
from ..service import DatasetQA
from .test_dataset_qa import action, collect, definition, engine, load, session
from .test_decisions import BareDialogue, configured, payload, text
from .test_planning import approve
from .test_workflow_input import generic_tools


def test_explicit_root_pointer_survives_an_editable_plan_roundtrip():
    tools = generic_tools()
    plan = compile_workflow(Workflow(steps=[{"key": "fetch", "tool": "retrieve"},
        {"key": "convert", "tool": "transform", "object": {"step": "fetch", "path": ""}}]), tools)
    saved = {"revision": 1, "spec": plan.model_dump(), "operations": {"fetch": "a", "convert": "b"}}
    shown = plan_view(saved, Operations())
    rebuilt = compile_workflow(plan_input(shown), tools, saved)
    assert rebuilt.steps[-1].object.path == ""  # Not the producer's default /file.
    assert rebuilt.model_dump() == plan.model_dump()


@pytest.mark.parametrize("field", ["checks", "targets"])
def test_boolean_and_numeric_outcome_constraints_are_not_interchangeable(field):
    old = Plan(outcomes=[{"key": "out", "description": "keep a boolean", "kind": "inspect",
        field: [{"path": "/flag", "test": "equals", "value": True}]}],
        steps=[{"key": "read", "tool": "inspect", "produces": ["out"]}])
    changed = old.model_copy(deep=True)
    getattr(changed.outcomes[0], field)[0].value = 1
    with pytest.raises(QAError, match="原有要求"):
        validate_revision({"spec": old.model_dump()}, changed)


def test_boolean_numeric_argument_revision_is_not_silently_discarded(engine):
    async def run():
        backend = configured()
        backend.catalog["data"].append(definition("evaluate", {"value": {"type": ["boolean", "number"]}}, ["value"]))
        service = DatasetQA(engine, BareDialogue(), backend.gateway())
        try:
            async with service.gateway.session() as tools:
                await tools.load("data", query="evaluate")
                state, execution = {}, Execution()
                sid = session(service)
                first = Workflow(steps=[{"key": "calc", "tool": "evaluate", "arguments": {"value": True}}])
                await install_plan(service, "alice", sid, first, tools, execution, state, {})
                revised = first.model_copy(deep=True)
                revised.steps[0].arguments["value"] = 1
                await install_plan(service, "alice", sid, revised, tools, execution, state, {})
                assert state["plan"]["revision"] == 2
                assert type(state["plan"]["spec"]["steps"][0]["arguments"]["value"]) is int
                operation = execution.operations.items[0]
                operation.update(state="succeeded", attempts=[{"key": "done", "state": "succeeded", "result_id": "done:0"}])
                with pytest.raises(QAError, match="已执行"):
                    await install_plan(service, "alice", sid, first, tools, execution, state, {})
        finally:
            await service.close()
    asyncio.run(run())


@pytest.mark.parametrize("stale_receipt", [False, True])
def test_coalesced_source_binding_remains_valid_when_an_old_alias_is_removed(engine, monkeypatch, stale_receipt):
    if stale_receipt:
        import scientific_agents.dataset_qa.service as service_module
        original_install = service_module.install_plan
        async def legacy_metadata(*args, **kwargs):
            await original_install(*args, **kwargs)
            for item in args[5].operations.items:
                if item["capability"]["name"] == "inspect":
                    item["plan_step"] = "retired_alias"
        monkeypatch.setattr(service_module, "install_plan", legacy_metadata)
    async def run():
        backend = configured()
        backend.catalog["data"][1].annotations = {"readOnlyHint": True, "idempotentHint": True}
        original = {"steps": [
            {"key": "find", "tool": "search", "arguments": {"query": "resources"}},
            {"key": "a", "tool": "inspect", "inputs": {"reference": {"step": "find", "path": "/items/0/id"}}},
            {"key": "b", "tool": "inspect", "inputs": {"reference": {"step": "find", "path": "/items/0/id"}}},
            {"key": "preview", "tool": "preview", "object": {"step": "a", "path": ""}},
            {"key": "sample", "tool": "sample", "arguments": {"count": 3}, "object": {"step": "b", "path": ""}}]}
        revised = deepcopy(original)
        revised["steps"] = [step for step in revised["steps"] if step["key"] != "a"]
        revised["steps"][-2]["object"]["step"] = "b"
        dialogue = BareDialogue(load(), action("remember", plan=original),
            action("remember", plan=revised), approve, text())
        service = DatasetQA(engine, dialogue, backend.gateway())
        try:
            sid = session(service)
            events = await collect(service, sid, "find resources, inspect one, then preview and sample it")
            saved = payload(service, sid, events)
            assert not saved.get("error")
            assert [name for _, name, _ in backend.calls] == ["search", "inspect", "preview", "sample"]
            assert all(args["reference"] == "a" for _, name, args in backend.calls if name != "search")
            assert len(saved["operations"]) == 4  # Duplicate inspection is still coalesced.
        finally:
            await service.close()
    asyncio.run(run())
