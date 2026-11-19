"""Atomic scope is explicit in the offered schema without changing wire admission."""
from copy import deepcopy
from types import SimpleNamespace

from jsonschema import Draft202012Validator
import pytest

from ..capabilities import SUPPORTING, TASK, definition
from ..execution import Execution
from ..mcp import Tool
from ..service import DatasetQA


@pytest.mark.parametrize("declared_goal", [False, True])
def test_atomic_task_projection_preserves_upstream_conditions_and_declared_scope(declared_goal):
    upstream = {"not": {"required": ["forbidden"]}}
    tool = Tool("records", "inspect", "Inspect a record", {"type": "object",
        "properties": {"reference": {"type": "string"}}, "required": ["reference"],
        "allOf": [upstream]}, {}, {"piflow": {"qa": {"atomic": True}}})
    execution = Execution()
    if declared_goal:
        execution.operations.register("Inspect the requested record", {"server": tool.server, "name": tool.name},
            None, planned=True)
    original = definition(tool)
    snapshot = deepcopy(original)
    offered, = DatasetQA._definitions([original], SimpleNamespace(loaded={tool.alias: tool}), execution)
    schema = offered["function"]["parameters"]
    assert schema["allOf"] == [upstream]
    assert (TASK in schema["required"]) is not declared_goal
    assert original == snapshot
    assert Draft202012Validator(schema).is_valid({"reference": "verified", TASK: {"complete_request": True}})
    assert not Draft202012Validator(schema).is_valid({"reference": "verified", "forbidden": True,
        TASK: {"complete_request": True}})
    # Old supporting-only calls remain a valid runtime contract. With no
    # declared goal, the model is offered the clearer explicit task contract.
    supporting = {"reference": "verified", SUPPORTING: True}
    assert Draft202012Validator(original["function"]["parameters"]).is_valid(supporting)
    assert Draft202012Validator(schema).is_valid(supporting) is declared_goal


def test_atomic_task_projection_removes_empty_qa_only_allof():
    tool = Tool("records", "inspect", "Inspect", {"type": "object", "properties": {}}, {},
        {"piflow": {"qa": {"atomic": True}}})
    offered, = DatasetQA._definitions([definition(tool)], SimpleNamespace(loaded={tool.alias: tool}), Execution())
    assert "allOf" not in offered["function"]["parameters"]
    assert offered["function"]["parameters"]["required"] == [TASK]
