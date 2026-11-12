"""Model-facing plans compile to strict execution contracts across domains."""
import asyncio
from copy import deepcopy
import json
from types import SimpleNamespace

import pytest
from jsonschema import Draft202012Validator
from pydantic import ValidationError

from mcp_servers.corpus_mcp import mcp
from ..capabilities import TASK
from ..contracts import QAError, Server
from ..dialogue import Remember, builtin_definitions
from ..execution import Execution
from ..mcp import MCPGateway, Tool, ToolSession
from ..plan_runtime import compile_workflow, install_plan, workflow_definition
from ..planning import Plan, Workflow, validate_revision
from ..service import DatasetQA
from .test_dataset_qa import action, collect, engine, result_cards, session
from .test_decisions import BareDialogue, configured, payload, text
from .test_file_pipeline import files, query_args
from .test_local_artifacts import download_client, file_plan
from .test_planning import approve, specimen


def compact_plan(threshold=80, limit=1000):
    return {"steps": [
        {"key": "query", "tool": "query_pubchem_compounds",
            "arguments": query_args(similarity_threshold=threshold, limit=limit)},
        {"key": "export", "tool": "export_dataset", "arguments": {"format": "csv"}, "object": "query"}]}


def generic_tools():
    def make(name, **qa):
        return Tool("archive", name, name, {"type": "object", "properties": {}}, {},
            {"piflow": {"qa": qa}})
    tools = [make("retrieve", artifact={"path": "/file"}, result={"kind": "records"}, plan_required=True),
        make("transform", artifact={"path": "/output", "consume": "source"},
            bind={"source": ["/id"]}, result={"kind": "converted"}),
        make("list", collection="/items", result={"kind": "collection"}),
        make("inspect", result={"kind": "schema"})]
    tools[1].schema["properties"]["source"] = {"type": "string"}
    return SimpleNamespace(loaded={tool.alias: tool for tool in tools})


@pytest.mark.parametrize("source", [None, "fetch", {"step": "fetch"}, {"step": "fetch", "path": "/file"}])
def test_metadata_derives_dependencies_types_and_terminal_outcome(source):
    steps = [{"key": "fetch", "tool": "retrieve", "arguments": {"count": 100, "ratio": 0.8, "flag": False}},
        {"key": "convert", "tool": "transform", "arguments": {"dialect": "compact"}}]
    if source is not None:
        steps[1]["object"] = source
    original = deepcopy(steps)
    plan = compile_workflow(Workflow(steps=steps), generic_tools())
    assert steps == original
    assert plan.steps[0].arguments == original[0]["arguments"]
    assert type(plan.steps[0].arguments["flag"]) is bool
    assert plan.steps[1].object.model_dump() == {"step": "fetch", "path": "/file"}
    assert plan.steps[1].dependencies() == {"fetch"}
    assert plan.steps[0].produces == []
    assert [(o.key, o.kind) for o in plan.outcomes] == [("convert", "converted")]


def test_multiple_sources_require_choice_and_do_not_assume_collection_member():
    tools = generic_tools()
    steps = [{"key": "a", "tool": "retrieve"}, {"key": "b", "tool": "retrieve"},
        {"key": "c", "tool": "transform"}]
    with pytest.raises(QAError, match="多个可用来源"):
        compile_workflow(Workflow(steps=steps), tools)
    steps[2]["object"] = "b"
    plan = compile_workflow(Workflow(steps=steps), tools)
    assert plan.steps[2].object.step == "b"
    assert {o.key for o in plan.outcomes} == {"a", "c"}
    steps = [{"key": "a", "tool": "list"}, {"key": "b", "tool": "inspect", "object": "a"}]
    with pytest.raises(QAError, match="对象位置"):
        compile_workflow(Workflow(steps=steps), tools)
    steps[1]["object"] = {"step": "a", "path": "/items/0"}
    assert compile_workflow(Workflow(steps=steps), tools).steps[1].object.path == "/items/0"


@pytest.mark.parametrize("steps", [
    [{"key": "a", "tool": "retrieve", "depends_on": ["a"]}],
    [{"key": "a", "tool": "retrieve", "depends_on": ["missing"]}],
    [{"key": "a", "tool": "retrieve", "deliver": False}],
    [{"key": "a", "tool": "retrieve"}, {"key": "a", "tool": "inspect"}],
    [{"key": "a", "tool": "retrieve", "produces": ["invented"]}],
])
def test_invalid_graphs_and_internal_bookkeeping_are_not_accepted(steps):
    with pytest.raises(ValidationError):
        compile_workflow(Workflow(steps=steps), generic_tools())


def test_scalar_bindings_and_explicit_intermediate_delivery():
    workflow = Workflow(steps=[{"key": "a", "tool": "retrieve", "deliver": True},
        {"key": "b", "tool": "inspect", "inputs": {"limit": {"step": "a", "path": "/count"}}}])
    plan = compile_workflow(workflow, generic_tools())
    assert {o.key for o in plan.outcomes} == {"a", "b"}
    assert plan.steps[1].dependencies() == {"a"}
    assert plan.steps[1].inputs["limit"].path == "/count"


def test_prerequisite_constraints_are_preserved_and_checks_never_discarded():
    steps = [{"key": "a", "tool": "retrieve", "constraints": ["retain units"]},
        {"key": "b", "tool": "transform"}]
    assert compile_workflow(Workflow(steps=steps), generic_tools()).outcomes[0].constraints == ["retain units"]
    steps[0]["checks"] = [{"path": "/file"}]
    with pytest.raises(QAError, match="验收条件"):
        compile_workflow(Workflow(steps=steps), generic_tools())
    steps[0]["deliver"] = True
    assert compile_workflow(Workflow(steps=steps), generic_tools()).outcomes[0].checks[0].path == "/file"


def test_revision_preserves_legacy_identities_constraints_and_checks():
    tools = generic_tools()
    prior = compile_workflow(Workflow(steps=[{"key": "a", "tool": "retrieve"},
        {"key": "b", "tool": "transform", "constraints": ["retain units"],
         "checks": [{"path": "/output/format", "test": "equals", "value": "csv"}]}]), tools)
    prior.outcomes[0].key = "legacy_outcome"
    prior.steps[1].produces = ["legacy_outcome"]
    saved = {"spec": prior.model_dump()}
    updated = compile_workflow(Workflow(steps=[{"key": "a", "tool": "retrieve"},
        {"key": "b", "tool": "transform"}]), tools, saved)
    assert updated.outcomes == prior.outcomes
    validate_revision(saved, updated)
    assert isinstance(Remember.model_validate({"plan": prior.model_dump()}).plan, Plan)
    assert isinstance(Remember.model_validate({"plan": {"steps": [{"key": "a", "tool": "retrieve"}]}}).plan, Workflow)


def test_plan_entry_advertises_business_schemas_without_forbidden_native_action():
    tools = generic_tools()
    original = next(d for d in builtin_definitions(True) if d["function"]["name"] == "remember")
    definition = workflow_definition(original, tools.loaded)["function"]
    schema = definition["parameters"]
    Draft202012Validator.check_schema(schema)
    assert "outcomes" not in schema["$defs"]["Workflow"]["properties"]
    assert "produces" not in schema["$defs"]["WorkflowStep"]["properties"]
    catalogue = json.loads(definition["description"].split("Catalogue: ", 1)[1])
    producer = next(t for t in tools.loaded.values() if t.name == "retrieve")
    assert catalogue[0]["tool"] == producer.alias
    assert catalogue[0]["arguments_schema"] == producer.schema
    assert "Catalogue:" not in original["function"]["description"]
    actions = Execution().actions(tools.loaded)
    assert producer.alias not in actions and "remember" in actions
    assert {t.alias for t in tools.loaded.values() if t.name != "retrieve"} <= actions


def test_same_session_compact_plans_keep_changed_conditions_and_csv(engine, files, download_client, monkeypatch):
    calls = []
    original = ToolSession.call
    async def capture(tools, alias, arguments, **kwargs):
        calls.append((tools.loaded[alias].name, deepcopy(arguments)))
        return await original(tools, alias, arguments, **kwargs)
    monkeypatch.setattr(ToolSession, "call", capture)

    async def run():
        service = DatasetQA(engine, BareDialogue(), MCPGateway({"piflow-corpus": Server(mcp)}))
        sid = session(service)
        try:
            for threshold, limit in [(80, 1000), (90, 100)]:
                def understand(messages, definitions):
                    assert not any(d["function"]["name"].endswith("_query_pubchem_compounds") for d in definitions)
                    remember = next(d["function"] for d in definitions if d["function"]["name"] == "remember")
                    assert "query_pubchem_compounds" in remember["description"]
                    assert "similarity_threshold" in remember["description"]
                    return action("remember", plan=compact_plan(threshold, limit))
                service.dialogue = BareDialogue(understand, approve, text())
                events = await collect(service, sid, f"PubChem similarity {threshold}, {limit} records as CSV", rid=str(threshold))
                saved = payload(service, sid, events)
                assert not saved.get("error")
                assert saved["plan"]["acceptance"]["export"]["state"] == "accepted"
                assert len(service.dialogue.inputs) == 3
                assert len(saved["operations"]) == 2
                output = result_cards(events)[0]["data"]["items"][0]
                assert output["resource"]["format"] == "csv"
                assert download_client.get(output["downloadUrl"]).status_code == 200
            assert [name for name, _ in calls] == ["query_pubchem_compounds", "export_dataset"] * 2
            assert calls[0][1] == query_args() and calls[2][1] == query_args(similarity_threshold=90, limit=100)
            assert calls[1][1]["source_ref"] != calls[3][1]["source_ref"]
        finally:
            await service.close()
    asyncio.run(run())


def test_planning_transition_does_not_spend_parameter_correction_budget(engine, files, monkeypatch):
    corrections = []
    original = Execution.correct
    def correct(self, error, limit):
        corrections.append(error.code)
        return original(self, error, limit)
    monkeypatch.setattr(Execution, "correct", correct)

    async def run():
        gateway = MCPGateway({"piflow-corpus": Server(mcp)})
        async with gateway.session() as tools:
            catalogue = await tools.tools("piflow-corpus")
        alias = next(t.alias for t in catalogue if t.name == "query_pubchem_compounds")
        # Recreate the two logged validation categories without claiming to
        # know the exact model arguments omitted from the production log.
        bad_kind = file_plan()
        bad_kind["steps"] = [bad_kind["steps"][0]]
        bad_kind["steps"][0]["produces"] = ["file"]
        orphan = file_plan()
        orphan["steps"][1].pop("object")
        def repair(messages, definitions):
            assert not files.requests
            return action("remember", plan=compact_plan())
        dialogue = BareDialogue(action(alias, **query_args(), **{TASK: {"complete_request": True}}),
            action("remember", plan=bad_kind), action("remember", plan=orphan), repair, approve, text())
        service = DatasetQA(engine, dialogue, gateway)
        try:
            sid = session(service)
            events = await collect(service, sid, "PubChem compounds as CSV")
            assert not payload(service, sid, events).get("error")
            assert corrections == ["invalid_parameters", "invalid_parameters"]
            assert result_cards(events)[0]["data"]["items"][0]["resource"]["format"] == "csv"
        finally:
            await service.close()
    asyncio.run(run())


def test_compact_revision_reuses_legacy_plan_without_new_revision(engine, files):
    async def run():
        service = DatasetQA(engine, BareDialogue(), MCPGateway({"piflow-corpus": Server(mcp)}))
        try:
            async with service.gateway.session() as tools:
                await tools.load("piflow-corpus", query="PubChem CSV")
                state, execution = {}, Execution()
                sid = session(service)
                await install_plan(service, "alice", sid, Plan.model_validate(file_plan()), tools, execution, state, {})
                before = deepcopy(state["plan"])
                await install_plan(service, "alice", sid, Workflow.model_validate(compact_plan()), tools, execution, state, {})
                assert state["plan"] == before
        finally:
            await service.close()
    asyncio.run(run())


def test_compact_repair_does_not_reexecute_completed_legacy_steps(engine):
    async def run():
        backend = configured()
        wrong = specimen()
        wrong["steps"][-1]["object"]["path"] = "/absent"
        compact = {"steps": [{k: v for k, v in step.items() if k != "produces"} for step in specimen()["steps"]]}
        def repair(messages, definitions):
            assert [call[1] for call in backend.calls] == ["search", "inspect"]
            return action("remember", plan=compact)
        dialogue = BareDialogue(action("load_mcp_tools", server="data"), action("remember", plan=wrong),
            approve, repair, approve, text())
        service = DatasetQA(engine, dialogue, backend.gateway())
        try:
            sid = session(service)
            events = await collect(service, sid, "检索资源，查看第一个的详情和三条样例")
            saved = payload(service, sid, events)
            assert not saved.get("error")
            assert [call[1] for call in backend.calls] == ["search", "inspect", "sample"]
            assert len(result_cards(events)) == 2
            assert saved["plan"]["revision"] == 2
            assert saved["plan"]["spec"]["outcomes"][1]["constraints"] == ["最多三条"]
        finally:
            await service.close()
    asyncio.run(run())
