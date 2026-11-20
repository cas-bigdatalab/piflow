"""Current source requirements survive native/Plan boundaries and every revision."""
import asyncio
from copy import deepcopy

from jsonschema import Draft202012Validator
from pydantic import ValidationError
import pytest

from ..capabilities import TASK
from ..contracts import QAError
from ..dialogue import Goal
from ..execution import Execution
from ..plan_runtime import _existing_goal, compile_workflow, install_plan
from ..planning import FromStep, Plan, SourceRequirements, Step, Workflow, plan_input, plan_view, validate_revision
from ..search import TaskDirective
from .test_dataset_qa import engine
from .test_goal_plan_migration import goal, workflow, world
from .test_plan_task_annotations import annotated_workflow, atomic_tools
from .test_workflow_input import generic_tools


REQUIREMENTS = {"criteria": {"threshold": 90, "limit": 100, "enabled": False,
    "range": {"min": -1, "max": 5}}, "fields": ["id", "mass"]}


def declared(value=REQUIREMENTS):
    return Workflow(steps=[{"key": "fetch", "tool": "retrieve"},
        {"key": "convert", "tool": "transform", "source_requirements": deepcopy(value)}])


def test_source_contract_is_bounded_nonrecursive_and_explicit_about_nulls():
    schema = SourceRequirements.model_json_schema()
    assert schema["required"] == ["criteria", "fields"]
    assert "$defs" not in schema
    validator = Draft202012Validator(schema)
    assert validator.is_valid({"criteria": None, "fields": None})
    assert not validator.is_valid({"criteria": None})
    assert not validator.is_valid({"fields": None})
    value = SourceRequirements(criteria=REQUIREMENTS["criteria"], fields=["id", "mass", "id"])
    assert value.model_dump() == REQUIREMENTS


@pytest.mark.parametrize("previous,current,allowed", [
    ({"criteria": None, "fields": None}, REQUIREMENTS, True),
    ({"criteria": {}, "fields": None}, {"criteria": None, "fields": None}, True),
    ({"criteria": {"threshold": 90}, "fields": None}, REQUIREMENTS, True),
    ({"criteria": None, "fields": ["id", "mass"]}, REQUIREMENTS, True),
    (REQUIREMENTS, {**REQUIREMENTS, "criteria": {**REQUIREMENTS["criteria"], "mode": "exact"}}, True),
    (REQUIREMENTS, {"criteria": None, "fields": None}, False),
    ({"criteria": {"threshold": 90}, "fields": None}, {"criteria": {}, "fields": None}, False),
    ({"criteria": {"enabled": False}, "fields": None}, {"criteria": {"enabled": 0}, "fields": None}, False),
    ({"criteria": {"range": {"min": -1}}, "fields": None},
        {"criteria": {"range": {"min": -1, "max": 5}}, "fields": None}, False),
    ({"criteria": None, "fields": ["id", "mass"]}, {"criteria": None, "fields": ["mass", "id"]}, False),
    ({"criteria": None, "fields": []}, {"criteria": None, "fields": None}, False),
])
def test_constraints_can_be_added_without_reinterpreting_declared_values(previous, current, allowed):
    assert SourceRequirements.model_validate(current).refines(SourceRequirements.model_validate(previous)) is allowed


@pytest.mark.parametrize("value", [{"criteria": None}, {"fields": None},
    {"criteria": {"x": float("nan")}, "fields": None},
    {"criteria": {"nested": [{1: "invalid"}]}, "fields": None},
    {"criteria": {"tuple": (1, 2)}, "fields": None},
    {"criteria": {"x": "x" * 6000}, "fields": None},
    {"criteria": None, "fields": ["x"] * 257},
    {"criteria": None, "fields": [""]}, {"criteria": None, "fields": ["x" * 201]},
    {"criteria": None, "fields": [1]}, {"criteria": [], "fields": None}])
def test_invalid_source_requirements_fail_before_execution(value):
    with pytest.raises(ValidationError):
        SourceRequirements.model_validate(value)


@pytest.mark.parametrize("value", [REQUIREMENTS, {"criteria": None, "fields": None}])
def test_source_requirements_roundtrip_through_native_goal_workflow_and_editable_plan(value):
    assert Goal(description="Export", tool="transform", source_requirements=value).model_dump()["source_requirements"] == value
    assert TaskDirective(complete_request=True, source_requirements=value).model_dump()["source_requirements"] == value
    tools = generic_tools()
    plan = compile_workflow(declared(value), tools)
    saved = {"spec": plan.model_dump(), "revision": 1, "operations": {"fetch": "op1", "convert": "op2"}}
    shown = plan_view(saved, Execution().operations)
    assert shown["editable"]["steps"][-1]["source_requirements"] == value
    rebuilt = compile_workflow(plan_input(shown), tools, saved)
    assert rebuilt.steps[-1].source_requirements.model_dump() == value
    omitted = declared(value).model_dump()
    omitted["steps"][-1].pop("source_requirements")
    inherited = compile_workflow(Workflow.model_validate(omitted), tools, saved)
    validate_revision(saved, inherited)
    assert inherited.steps[-1].source_requirements.model_dump() == value


@pytest.mark.parametrize("replacement", [None, {"criteria": None, "fields": None},
    {**REQUIREMENTS, "criteria": {**REQUIREMENTS["criteria"], "threshold": 80}},
    {**REQUIREMENTS, "criteria": {**REQUIREMENTS["criteria"], "enabled": 0}},
    {**REQUIREMENTS, "fields": ["id"]}])
def test_revision_cannot_drop_or_change_current_source_scope(replacement):
    original = compile_workflow(declared(), generic_tools())
    changed = original.model_dump()
    changed["steps"][-1]["source_requirements"] = replacement
    with pytest.raises(QAError):
        validate_revision({"spec": original.model_dump()}, Plan.model_validate(changed))


@pytest.mark.parametrize("previous", [{"criteria": None, "fields": None},
    {"criteria": {"threshold": 90}, "fields": None}])
def test_workflow_revision_can_add_constraints_and_retains_them_when_omitted(previous):
    tools = generic_tools()
    original = compile_workflow(declared(previous), tools)
    saved = {"spec": original.model_dump()}
    refined = compile_workflow(declared(), tools, saved)
    validate_revision(saved, refined)
    saved["spec"] = refined.model_dump()
    omitted = declared().model_dump()
    omitted["steps"][-1].pop("source_requirements")
    inherited = compile_workflow(Workflow.model_validate(omitted), tools, saved)
    validate_revision(saved, inherited)
    assert inherited.steps[-1].source_requirements.model_dump() == REQUIREMENTS


def test_renaming_an_export_step_cannot_erase_its_declared_scope():
    original = compile_workflow(declared(), generic_tools())
    changed = original.model_dump()
    changed["steps"][-1].update(key="different", source_requirements=None)
    with pytest.raises(QAError, match="步骤标识"):
        validate_revision({"spec": original.model_dump()}, Plan.model_validate(changed))


def test_atomic_native_annotation_lifts_source_requirements_without_losing_nulls():
    value = {"criteria": None, "fields": None}
    native = annotated_workflow({"complete_request": True, "source_requirements": value})
    plan = compile_workflow(native, atomic_tools())
    assert TASK not in plan.steps[-1].arguments
    assert plan.steps[-1].source_requirements.model_dump() == value
    native.steps[-1].source_requirements = SourceRequirements.model_validate(REQUIREMENTS)
    with pytest.raises(QAError) as error:
        compile_workflow(native, atomic_tools())
    assert error.value.detail["field"] == "source_requirements"


def test_atomic_annotation_can_strengthen_step_constraints_without_loss():
    native = annotated_workflow({"complete_request": True, "source_requirements": REQUIREMENTS})
    native.steps[-1].source_requirements = SourceRequirements(criteria={"threshold": 90}, fields=None)
    plan = compile_workflow(native, atomic_tools())
    assert plan.steps[-1].source_requirements.model_dump() == REQUIREMENTS


@pytest.mark.parametrize("declared_first", [False, True])
def test_installation_and_goal_migration_preserve_typed_scope_in_operation_intent(engine, declared_first):
    async def run():
        async with world(engine) as (service, tools, execution, state, sid, backend):
            spec = workflow(source_requirements=REQUIREMENTS)
            if declared_first:
                existing = goal(execution, tools)
                existing["intent"] = {"source_requirements": deepcopy(REQUIREMENTS)}
                spec = workflow(goal=existing["id"])
            await install_plan(service, "alice", sid, spec, tools, execution, state, {})
            assert len(execution.operations.items) == 1 and not backend.calls
            operation, = execution.operations.items
            assert operation["intent"]["source_requirements"] == REQUIREMENTS
            assert state["plan"]["spec"]["steps"][0]["source_requirements"] == REQUIREMENTS
            shown = plan_view(state["plan"], execution.operations)
            before = deepcopy(state)
            await install_plan(service, "alice", sid, plan_input(shown), tools, execution, state, {})
            assert state == before and not backend.calls
    asyncio.run(run())


def test_goal_migration_preserves_new_constraints_instead_of_overwriting_with_old_intent(engine):
    async def run():
        async with world(engine) as (service, tools, execution, state, sid, backend):
            existing = goal(execution, tools)
            existing["intent"] = {"source_requirements": {"criteria": {"threshold": 90}, "fields": None}}
            await install_plan(service, "alice", sid,
                workflow(goal=existing["id"], source_requirements=REQUIREMENTS), tools, execution, state, {})
            operation, = execution.operations.items
            assert operation["intent"]["source_requirements"] == REQUIREMENTS
            assert state["plan"]["spec"]["steps"][0]["source_requirements"] == REQUIREMENTS
            assert not backend.calls
    asyncio.run(run())


def rejected_export():
    tools = atomic_tools()
    tool = next(tool for tool in tools.loaded.values() if tool.name == "transform")
    execution = Execution()
    key = execution.operations.register("Export matching records", {"server": tool.server, "name": tool.name},
        {"result_id": "old", "path": ""}, planned=True)
    item = execution.operations.get(key)
    item["intent"] = {"operation": "export", "source_requirements": deepcopy(REQUIREMENTS)}
    execution.operations.reject(key, "rejected", QAError("invalid_parameters", "Incompatible source",
        detail={"origin": "source_requirements"}))
    step = Step(key="export", tool=tool.alias, goal=key, object=FromStep(step="fresh"))
    return tool, execution, item, step


def test_explicit_unexecuted_rejected_export_can_bind_a_new_producer():
    tool, execution, item, step = rejected_export()
    assert _existing_goal(step, tool, {}, None, execution.operations, set()) is item
    step.source_requirements = SourceRequirements.model_validate(REQUIREMENTS)
    assert _existing_goal(step, tool, {}, None, execution.operations, set()) is item


@pytest.mark.parametrize("mutation", ["implicit", "executed", "unknown", "other_failure", "changed_scope"])
def test_rejected_source_retargeting_never_replays_success_or_changes_requirements(mutation):
    tool, execution, item, step = rejected_export()
    if mutation == "implicit":
        step.goal = None
        assert _existing_goal(step, tool, {}, None, execution.operations, set()) is None
        return
    if mutation == "executed":
        item["attempts"][0].update(state="succeeded", dispatched=True)
    if mutation == "unknown":
        item["state"] = "unknown"
    if mutation == "other_failure":
        item["attempts"][0]["error"]["detail"]["origin"] = "object_binding"
    if mutation == "changed_scope":
        step.source_requirements = SourceRequirements(criteria={"threshold": 80}, fields=REQUIREMENTS["fields"])
    with pytest.raises(QAError):
        _existing_goal(step, tool, {}, None, execution.operations, set())
