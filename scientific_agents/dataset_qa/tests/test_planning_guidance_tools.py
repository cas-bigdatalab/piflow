"""Hidden planning capabilities retain their execution contract."""
from copy import deepcopy
import json

from ..dialogue import builtin_definitions
from ..plan_runtime import workflow_definition
from .test_workflow_input import generic_tools


def test_hidden_catalogue_preserves_execution_modes_without_changing_wire_schemas():
    tools = generic_tools()
    original = deepcopy(next(item for item in builtin_definitions(planning=True)
        if item["function"]["name"] == "remember"))
    shown = workflow_definition(original, tools.loaded)
    catalogue = json.loads(shown["function"]["description"].split("Catalogue: ", 1)[1])
    by_alias = {item["tool"]: item for item in catalogue}
    for alias, tool in tools.loaded.items():
        expected = "plan_required" if tool.name == "retrieve" else "direct_allowed"
        assert by_alias[alias]["execution_mode"] == expected
    # Explanatory catalogue data does not add business arguments or alter the
    # shared remember definition used by a different task.
    assert shown["function"]["parameters"] == original["function"]["parameters"]
    assert "Catalogue: " not in original["function"]["description"]
    assert all("execution_mode" not in tool.schema.get("properties", {}) for tool in tools.loaded.values())


def test_visible_native_tools_are_not_repeated_in_the_hidden_catalogue():
    tools = generic_tools()
    remember = next(item for item in builtin_definitions(planning=True) if item["function"]["name"] == "remember")
    visible = {alias for alias, tool in tools.loaded.items() if tool.name != "retrieve"}
    shown = workflow_definition(remember, tools.loaded, visible)
    catalogue = json.loads(shown["function"]["description"].split("Catalogue: ", 1)[1])
    assert len(catalogue) == 1 and catalogue[0]["execution_mode"] == "plan_required"
    assert catalogue[0]["tool"] not in visible
