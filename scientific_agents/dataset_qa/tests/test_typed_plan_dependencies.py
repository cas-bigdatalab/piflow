"""Typed dependency compilation uses declared bindings, never guessed identifiers."""
import asyncio
from copy import deepcopy
import json

import pytest
from jsonschema import Draft202012Validator

from ..contracts import QAError
from ..planning import Workflow
from ..plan_runtime import compile_workflow, install_plan, workflow_definition
from ..dialogue import builtin_definitions
from ..execution import Execution
from ..service import DatasetQA
from .test_dataset_qa import action, collect, engine, load, session
from .test_decisions import BareDialogue, configured, payload, text
from .test_planning import approve
from .test_workflow_input import generic_tools


def workflow(path="/file"):
    return Workflow(steps=[{"key": "fetch", "tool": "retrieve"},
        {"key": "convert", "tool": "transform",
         "inputs": {"source": {"step": "fetch", "path": path}}}])


@pytest.mark.parametrize("path", ["", "/file"])
def test_declared_object_to_scalar_uses_authoritative_object_binding(path):
    intent = workflow(path)
    original = intent.model_dump()
    plan = compile_workflow(intent, generic_tools())
    assert plan.steps[-1].object.model_dump() == {"step": "fetch", "path": "/file"}
    assert not plan.steps[-1].inputs
    assert plan.steps[-1].dependencies() == {"fetch"}
    assert intent.model_dump() == original


def test_explicit_scalar_pointer_keeps_exact_value_semantics():
    plan = compile_workflow(workflow("/file/id"), generic_tools())
    assert plan.steps[-1].object is None
    assert plan.steps[-1].inputs["source"].path == "/file/id"


def test_planning_catalogue_exposes_declared_output_locations_and_value_semantics():
    tools = generic_tools()
    definition = next(item for item in builtin_definitions(True) if item["function"]["name"] == "remember")
    description = workflow_definition(definition, tools.loaded)["function"]["description"]
    catalogue = json.loads(description.split("Catalogue: ", 1)[1])
    producer = next(item for item in catalogue if item["tool"].endswith("_retrieve"))
    assert producer["result_locations"] == {"artifact": "/file"}
    consumer = next(item for item in catalogue if item["tool"].endswith("_transform"))
    assert consumer["object_bindings"] == {"source": ["/id"]}
    assert "scalar parameters need scalar paths" in description


@pytest.mark.parametrize("schema", [
    {"type": "object", "required": ["id"]},
    {"type": ["object", "string"]},
    {"anyOf": [{"type": "string"}, {"type": "object", "required": ["id"]}]},
    {"$ref": "#/$defs/record"},
])
def test_object_compatible_input_is_not_reinterpreted_as_identifier(schema):
    tools = generic_tools()
    consumer = next(t for t in tools.loaded.values() if t.name == "transform")
    consumer.schema["properties"]["source"] = schema
    consumer.schema["$defs"] = {"record": {"type": "object", "required": ["id"]}}
    plan = compile_workflow(workflow(), tools)
    assert plan.steps[-1].object is None
    assert plan.steps[-1].inputs["source"].path == "/file"


@pytest.mark.parametrize("schema", [
    {"$ref": "#/$defs/id"},
    {"allOf": [{"$ref": "#/$defs/id"}, {"minLength": 1}]},
    {"oneOf": [{"type": "string"}, {"type": "null"}]},
])
def test_schema_refs_and_scalar_unions_use_the_same_declared_mapping(schema):
    tools = generic_tools()
    consumer = next(t for t in tools.loaded.values() if t.name == "transform")
    consumer.schema["properties"]["source"] = schema
    consumer.schema["$defs"] = {"id": {"type": "string"}}
    assert compile_workflow(workflow(), tools).steps[-1].object.path == "/file"


@pytest.mark.parametrize("location", ["direct", "resource", "child"])
def test_nested_schema_resource_preserves_valid_object_inputs(location):
    tools = generic_tools()
    consumer = next(t for t in tools.loaded.values() if t.name == "transform")
    nested = {"$id": "urn:record-schema", "$defs": {"value": {"type": "object", "required": ["id"]}},
        "$ref": "#/$defs/value", "properties": {"value": {"$ref": "#/$defs/value"}}}
    consumer.schema["$defs"] = {"value": {"type": "string"}, "record": nested}
    consumer.schema["properties"]["source"] = nested if location == "direct" else {
        "$ref": "#/$defs/record" + ("/properties/value" if location == "child" else "")}
    assert Draft202012Validator(consumer.schema).is_valid({"source": {"id": "actual-identifier"}})
    plan = compile_workflow(workflow(), tools)
    assert plan.steps[-1].object is None
    assert plan.steps[-1].inputs["source"].path == "/file"


def test_root_schema_id_does_not_disable_local_scalar_reference_inference():
    tools = generic_tools()
    consumer = next(t for t in tools.loaded.values() if t.name == "transform")
    consumer.schema.update({"$id": "urn:tool-schema", "$defs": {"id": {"type": "string"}}})
    consumer.schema["properties"]["source"] = {"$ref": "#/$defs/id"}
    assert compile_workflow(workflow(), tools).steps[-1].object.path == "/file"


@pytest.mark.parametrize("paths", [[], ["/id", "/alternate"], [""]])
def test_missing_or_ambiguous_projection_is_rejected_before_execution(paths):
    tools = generic_tools()
    consumer = next(t for t in tools.loaded.values() if t.name == "transform")
    consumer.meta["piflow"]["qa"]["bind"] = {"source": paths} if paths else {}
    with pytest.raises(QAError) as error:
        compile_workflow(workflow(), tools)
    assert error.value.detail["phase"] == "plan_validation"
    assert error.value.detail["dispatched"] is False
    assert error.value.detail["source"] == {"step": "fetch", "path": "/file"}


def test_multiple_declared_output_objects_require_an_explicit_source_location():
    tools = generic_tools()
    producer = next(t for t in tools.loaded.values() if t.name == "retrieve")
    producer.meta["piflow"]["qa"]["object"] = "/another"
    with pytest.raises(QAError) as error:
        compile_workflow(workflow(""), tools)
    assert error.value.detail["candidate_paths"] == ["/file/id", "/another/id"]
    assert compile_workflow(workflow(), tools).steps[-1].object.path == "/file"


def test_object_input_cannot_silently_replace_a_different_selected_source():
    intent = workflow()
    intent.steps[-1].object = "selected-object"
    with pytest.raises(QAError) as error:
        compile_workflow(intent, generic_tools())
    assert error.value.detail["dispatched"] is False


def test_compilation_does_not_hide_duplicate_argument_and_dependency_values():
    intent = workflow()
    intent.steps[-1].arguments["source"] = "supplied-identifier"
    with pytest.raises(QAError) as error:
        compile_workflow(intent, generic_tools())
    assert error.value.detail["path"] == ["source"]
    assert error.value.detail["dispatched"] is False


def declared_backend(*, pointer="/items/0"):
    backend = configured()
    backend.catalog["data"][0].meta["piflow"]["qa"]["object"] = pointer
    backend.catalog["data"][1].meta["piflow"]["qa"]["bind"] = {"reference": ["/id"]}
    return backend


def record_workflow(pointer="/items/0"):
    return {"steps": [{"key": "fetch", "tool": "search", "arguments": {"query": "resources"}},
        {"key": "inspect", "tool": "inspect",
         "inputs": {"reference": {"step": "fetch", "path": pointer}}}]}


@pytest.mark.parametrize("strict", [False, True])
def test_workflow_and_strict_plan_bind_typed_sources_without_extra_decisions(engine, strict):
    async def run():
        backend = declared_backend()
        intent = record_workflow()
        if strict:
            intent["outcomes"] = [{"key": "answer", "description": "inspect the source", "kind": "inspect"}]
            intent["steps"][-1]["produces"] = ["answer"]
        dialogue = BareDialogue(load(), action("remember", plan=intent), approve, text())
        service = DatasetQA(engine, dialogue, backend.gateway())
        try:
            sid = session(service)
            events = await collect(service, sid, "find and inspect the resource")
            saved = payload(service, sid, events)
            assert not saved.get("error")
            assert [name for _, name, _ in backend.calls] == ["search", "inspect"]
            assert backend.calls[-1][2] == {"reference": "a"}
            assert len(dialogue.inputs) == 4
            assert all(len(op["attempts"]) == 1 for op in saved["operations"])
            assert saved["operations"][-1]["target"]["path"] == "/items/0"
        finally:
            await service.close()
    asyncio.run(run())


@pytest.mark.parametrize("failure", ["missing_id", "wrong_type", "input_check", "missing_object"])
def test_runtime_source_failure_can_be_repaired_without_repeating_successful_work(engine, failure):
    async def run():
        pointer = "/absent" if failure == "missing_object" else "/items/0"
        backend = declared_backend(pointer=pointer)
        if failure == "missing_id":
            backend.items[0].pop("id")
        elif failure == "wrong_type":
            backend.items[0]["id"] = {"nested": "not-an-identifier"}
        elif failure == "input_check":
            backend.items[0]["accepted"] = False
            backend.items[1]["accepted"] = True
            backend.catalog["data"][1].meta["piflow"]["qa"]["input_checks"] = [
                {"path": "/accepted", "test": "equals", "value": True}]
        intent = record_workflow(pointer)

        def repair(messages, definitions):
            assert [name for _, name, _ in backend.calls] == ["search"]
            if failure == "missing_object":
                decision = json.loads(messages[1].content)["plan"]["decisions"]["inspect"]
                assert decision["phase"] == "dependency_binding"
                assert decision["dispatched"] is False
                assert decision["object"] == {"step": "fetch", "path": "/absent"}
            else:
                feedback = [json.loads(m.content) for m in messages if m.type == "tool"][-1]
                assert feedback["detail"]["dispatched"] is False
                if failure == "wrong_type":
                    assert feedback["detail"]["actual_type"] == "object"
                if failure == "input_check":
                    assert feedback["detail"]["origin"] == "object_contract"
            fixed = deepcopy(intent)
            fixed["steps"][-1].pop("inputs")
            fixed["steps"][-1]["object"] = {"step": "fetch", "path": "/items/1"}
            return action("remember", plan=fixed)

        service = DatasetQA(engine, BareDialogue(load(), action("remember", plan=intent),
            approve, repair, approve, text()), backend.gateway())
        try:
            sid = session(service)
            events = await collect(service, sid, "find and inspect a compatible resource")
            saved = payload(service, sid, events)
            assert not saved.get("error")
            assert [name for _, name, _ in backend.calls] == ["search", "inspect"]
            assert backend.calls[-1][2] == {"reference": "b"}
            assert len(saved["operations"][0]["attempts"]) == 1
            assert saved["plan"]["revision"] == 2
            assert not saved["plan"].get("decisions")
        finally:
            await service.close()
    asyncio.run(run())


def test_static_ambiguity_keeps_installation_atomic(engine):
    async def run():
        backend = configured()
        backend.catalog["data"][0].meta["piflow"]["qa"]["object"] = "/items/0"
        service = DatasetQA(engine, BareDialogue(), backend.gateway())
        try:
            state, execution = {}, Execution()
            async with service.gateway.session() as tools:
                await tools.load("data")
                with pytest.raises(QAError) as error:
                    await install_plan(service, "alice", session(service),
                        Workflow.model_validate(record_workflow()), tools, execution, state, {})
                assert error.value.detail["candidate_paths"] == ["/items/0/id", "/items/0/reference"]
            assert not state and not execution.operations.items and not backend.calls
        finally:
            await service.close()
    asyncio.run(run())
