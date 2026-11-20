"""Planning/observation boundary and late source failures from production traces."""
import asyncio
from copy import deepcopy
import json

import pytest
from pydantic import ValidationError

from mcp_servers.corpus_mcp import mcp
from ..contracts import QAError, Server
from ..dialogue import Remember
from ..execution import Execution
from ..mcp import MCPGateway
from ..plan_runtime import compile_workflow, install_plan
from ..planning import Plan, Workflow, plan_input, plan_view
from ..service import DatasetQA
from .test_dataset_qa import action, collect, engine, load, result_cards, session
from .test_decisions import BareDialogue, configured, payload, text
from .test_file_pipeline import files
from .test_local_artifacts import download_client, file_plan
from .test_planning import approve, specimen
from .test_workflow_input import compact_plan, generic_tools


def test_dependency_order_does_not_reinterpret_a_literal_identifier():
    plan = compile_workflow(Workflow(steps=[{"key": "fetch", "tool": "retrieve"},
        {"key": "convert", "tool": "transform", "depends_on": ["fetch"], "arguments": {"source": "fetch"}}]), generic_tools())
    assert plan.steps[-1].object is None
    assert plan.steps[-1].arguments == {"source": "fetch"}
    assert plan.steps[0].produces == []
    independent = compile_workflow(Workflow(steps=[{"key": "fetch", "tool": "retrieve"},
        {"key": "convert", "tool": "transform", "arguments": {"source": "fetch"}}]), generic_tools())
    assert independent.steps[-1].arguments == {"source": "fetch"}
    assert independent.steps[-1].object is None


@pytest.mark.parametrize("legacy", [False, True])
def test_ungrounded_literal_consumer_is_rejected_before_running_prerequisites(engine, files, legacy):
    async def run():
        service = DatasetQA(engine, BareDialogue(), MCPGateway({"piflow-corpus": Server(mcp)}))
        try:
            async with service.gateway.session() as tools:
                await tools.load("piflow-corpus", query="PubChem CSV")
                plan = file_plan() if legacy else compact_plan()
                plan["steps"][-1].pop("object")
                plan["steps"][-1].update(depends_on=["query"], arguments={"format": "csv", "source_ref": "invented-source"})
                execution, state = Execution(), {}
                with pytest.raises(QAError) as error:
                    await install_plan(service, "alice", session(service), Remember(plan=plan).plan,
                        tools, execution, state, {})
                assert error.value.detail["step"] == "export"
                assert error.value.detail["fields"] == ["source_ref"]
                assert error.value.detail["source_steps"] == ["query"]
                assert error.value.detail["dispatched"] is False
                assert not files.requests and not files.writes and not execution.operations.items and not state
        finally:
            await service.close()
    asyncio.run(run())


@pytest.mark.parametrize("initial_source", ["query", "invented-source"])
def test_actual_file_pipeline_repairs_unbound_source_before_query(engine, files, download_client, initial_source):
    async def run():
        plan = compact_plan()
        plan["steps"][-1].pop("object")
        plan["steps"][-1].update(depends_on=["query"], arguments={"format": "csv", "source_ref": initial_source})
        def repair(messages, definitions):
            feedback = json.loads(messages[-1].content)["runtime_feedback"]
            assert feedback["detail"]["phase"] == "plan_validation"
            assert not files.requests
            fixed = deepcopy(plan)
            fixed["steps"][-1]["arguments"].pop("source_ref")
            fixed["steps"][-1]["object"] = feedback["detail"]["source_steps"][0]
            # Observation-shaped annotations must not consume a correction round.
            fixed["revision"] = 1
            for step in fixed["steps"]:
                step["state"] = "succeeded"
            return action("remember", plan=fixed)
        script = [action("remember", plan=plan), repair]
        service = DatasetQA(engine, BareDialogue(*script, approve, text()), MCPGateway({"piflow-corpus": Server(mcp)}))
        try:
            sid = session(service)
            events = await collect(service, sid, "PubChem filtered compounds exported as CSV")
            saved = payload(service, sid, events)
            assert not saved.get("error")
            assert saved["plan"]["acceptance"]["export"]["state"] == "accepted"
            assert len(service.dialogue.inputs) == 4
            assert len(saved["operations"]) == 2
            assert all([a["state"] for a in op["attempts"]] == ["succeeded"] for op in saved["operations"])
            result = result_cards(events)[0]["data"]["items"][0]
            assert result["resource"]["format"] == "csv"
            assert download_client.get(result["downloadUrl"]).status_code == 200
        finally:
            await service.close()
    asyncio.run(run())


@pytest.mark.parametrize("echo", ["editable", "whole_view", "legacy_view"])
def test_model_can_revise_observed_plan_without_copying_or_faking_execution(engine, echo):
    async def run():
        backend = configured()
        wrong = specimen()
        wrong["steps"][2]["object"]["path"] = "/absent"
        def repair(messages, definitions):
            assert [call[1] for call in backend.calls] == ["search", "inspect"]
            shown = json.loads(messages[1].content)["plan"]
            assert "steps" not in shown
            assert Workflow.model_validate(shown["editable"])
            assert shown["step_status"] == {"find": "succeeded", "detail": "succeeded", "sample": "pending"}
            if echo == "legacy_view":
                submitted = deepcopy(wrong)
                submitted["steps"][2]["object"]["path"] = "/items/0"
                submitted["revision"] = shown["revision"]
                for step in submitted["steps"]:
                    step["state"] = "succeeded"
            else:
                shown["editable"]["steps"][2]["object"]["path"] = "/items/0"
                shown["step_status"]["sample"] = "succeeded"
                submitted = shown if echo == "whole_view" else shown["editable"]
            return action("remember", plan=submitted)
        service = DatasetQA(engine, BareDialogue(load(), action("remember", plan=wrong), approve, repair, approve, text()), backend.gateway())
        try:
            sid = session(service)
            events = await collect(service, sid, "find, inspect the first resource and sample three records")
            saved = payload(service, sid, events)
            assert not saved.get("error")
            assert [call[1] for call in backend.calls] == ["search", "inspect", "sample"]
            assert saved["plan"]["revision"] == 2
            assert all(len(op["attempts"]) == 1 for op in saved["operations"])
            assert saved["plan"]["spec"]["outcomes"][1]["constraints"] == ["最多三条"]
        finally:
            await service.close()
    asyncio.run(run())


def test_readonly_annotations_do_not_relax_business_fields_or_unknown_fields():
    incoming = {"revision": 99, "steps": [{"key": "x", "tool": "arbitrary", "state": "succeeded",
        "arguments": {"state": "pending", "revision": 7, "flag": False, "count": 100}}]}
    original = deepcopy(incoming)
    parsed = plan_input(incoming)
    assert parsed.steps[0].arguments == original["steps"][0]["arguments"]
    assert incoming == original
    for mutation in (lambda p: p.update(unknown=True), lambda p: p["steps"][0].update(unknown=True)):
        invalid = deepcopy(incoming)
        mutation(invalid)
        with pytest.raises(ValidationError):
            plan_input(invalid)


def test_editable_view_roundtrips_without_changing_revision_or_outcome_constraints(engine):
    async def run():
        backend = configured()
        service = DatasetQA(engine, BareDialogue(), backend.gateway())
        try:
            async with service.gateway.session() as tools:
                await tools.load("data")
                execution, state = Execution(), {}
                sid = session(service)
                await install_plan(service, "alice", sid, Plan.model_validate(specimen()), tools, execution, state, {})
                before = deepcopy(state["plan"])
                shown = plan_view(state["plan"], execution.operations)
                await install_plan(service, "alice", sid, plan_input(shown), tools, execution, state, {})
                assert state["plan"] == before
        finally:
            await service.close()
    asyncio.run(run())


def test_legacy_accepted_plan_recovers_after_read_direct_attempt_and_annotated_revision(engine, files, download_client, monkeypatch):
    """Replay the logged sequence with a plan accepted by the earlier runtime."""
    import scientific_agents.dataset_qa.service as service_module

    original_install = service_module.install_plan
    seeded = False
    async def seed_legacy(*args, **kwargs):
        nonlocal seeded
        await original_install(*args, **kwargs)
        if not seeded:
            seeded = True
            saved = args[6]["plan"]
            step = saved["spec"]["steps"][-1]
            step.update(object=None, depends_on=["query"])
            step["arguments"]["source_ref"] = "unresolved-source"
    monkeypatch.setattr(service_module, "install_plan", seed_legacy)

    def read_saved(messages, definitions):
        feedback = json.loads(messages[-1].content)
        assert feedback["detail"]["phase"] == "input_binding"
        assert feedback["detail"]["dispatched"] is False
        assert len(files.requests) == 2  # One PubChem query and property fetch, no replay.
        context = json.loads(messages[1].content)
        rid = next(op for op in context["operations"]["items"] if op["state"] == "succeeded")["result_ids"][0]
        return action("read_result", result_id=rid)

    def mistaken_direct(messages, definitions):
        remember = next(d["function"] for d in definitions if d["function"]["name"] == "remember")
        catalog = json.loads(remember["description"].split("Catalogue: ", 1)[1])
        alias = next(row["tool"] for row in catalog if row["tool"].endswith("_export_dataset"))
        return action(alias, source_ref="unresolved-source", format="csv")

    def correct(messages, definitions):
        feedback = json.loads(messages[-1].content)["runtime_feedback"]
        assert feedback["detail"]["pending_steps"] == ["export"]
        view = json.loads(messages[1].content)["plan"]
        fixed = deepcopy(view["editable"])
        fixed["revision"] = view["revision"]
        for step in fixed["steps"]:
            step["state"] = view["step_status"][step["key"]]
        fixed["steps"][-1]["object"] = "query"
        fixed["steps"][-1]["arguments"].pop("source_ref")
        return action("remember", plan=fixed)

    async def run():
        dialogue = BareDialogue(action("remember", plan=compact_plan()), approve,
            read_saved, mistaken_direct, correct, approve, text())
        service = DatasetQA(engine, dialogue, MCPGateway({"piflow-corpus": Server(mcp)}))
        try:
            sid = session(service)
            events = await collect(service, sid, "PubChem compounds exported as CSV")
            saved = payload(service, sid, events)
            assert not saved.get("error")
            assert len(files.requests) == 2
            assert len(saved["operations"][0]["attempts"]) == 1
            assert [a["state"] for a in saved["operations"][1]["attempts"]] == ["rejected", "succeeded"]
            assert len(dialogue.inputs) == 7
            result = result_cards(events)[0]["data"]["items"][0]
            assert result["resource"]["format"] == "csv"
            assert download_client.get(result["downloadUrl"]).status_code == 200
        finally:
            await service.close()
    asyncio.run(run())
