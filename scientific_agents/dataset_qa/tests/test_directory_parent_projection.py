"""Directory guidance follows metadata without changing the upstream contract."""
from copy import deepcopy

from jsonschema import Draft202012Validator
import pytest

from ..capabilities import TASK, definition
from ..mcp import Tool


@pytest.mark.parametrize("parameter", ["parent_node", "container"])
def test_directory_parent_guidance_keeps_business_schema_and_literal_identifiers(parameter):
    schema = {"type": "object", "properties": {
        "dataset": {"type": "string"}, parameter: {
            "anyOf": [{"type": "string"}, {"type": "integer"}, {"type": "null"}],
            "default": None, "description": "Original provider guidance."}},
        "required": ["dataset"], "additionalProperties": False}
    tool = Tool("arbitrary-records", "children", "List children", schema, {}, {"piflow": {"qa": {
        "atomic": True, "directory": {"identity": ["dataset"], "parent": parameter,
            "nodes": ["/children"], "node_id": "/key", "name": "/label", "is_file": "/file"}}}})
    original = deepcopy(tool.schema)
    offered = definition(tool)["function"]["parameters"]
    field = offered["properties"][parameter]
    assert field["description"].startswith("Original provider guidance.")
    assert "Root: omit." in field["description"]
    assert "directory-node ID from this dataset/source" in field["description"]
    assert "examples" not in field and "default" not in field
    assert field["anyOf"] == [{"type": "string"}, {"type": "integer"}]
    assert tool.schema == original
    # Evidence admission validates identity later; schema guidance must not ban
    # legitimate literal identifiers or normalize them into a different value.
    validator = Draft202012Validator(offered)
    for identifier in ("None", "null", "root", 0, "actual-node"):
        validator.validate({"dataset": "verified", parameter: identifier, TASK: {"complete_request": True}})
    validator.validate({"dataset": "verified", TASK: {"complete_request": True}})
    assert not validator.is_valid({"dataset": "verified", parameter: None, TASK: {"complete_request": True}})
    # Explicit JSON null remains valid at the authoritative upstream boundary.
    Draft202012Validator(tool.schema).validate({"dataset": "verified", parameter: None})


@pytest.mark.parametrize("field", [
    {"type": ["string", "null"], "default": None, "examples": ["provider-node"]},
    {"type": "string", "default": None},
    {"type": ["string", "null"]},
])
def test_root_example_does_not_replace_provider_examples_or_invent_a_null_default(field):
    schema = {"type": "object", "properties": {"dataset": {"type": "string"}, "container": field}}
    tool = Tool("arbitrary-records", "children", "List children", schema, {}, {"piflow": {"qa": {
        "directory": {"identity": ["dataset"], "parent": "container",
            "nodes": ["/children"], "node_id": "/key", "name": "/label", "is_file": "/file"}}}})
    original = deepcopy(tool.schema)
    offered = definition(tool)["function"]["parameters"]["properties"]["container"]
    assert offered.get("examples") == field.get("examples")
    assert tool.schema == original


def test_parent_named_business_parameter_without_directory_metadata_is_unchanged():
    schema = {"type": "object", "properties": {"parent_node": {"type": "string", "description": "Business value"}}}
    tool = Tool("other", "operation", "Generic operation", schema, {}, {})
    assert definition(tool)["function"]["parameters"]["properties"]["parent_node"] == schema["properties"]["parent_node"]
