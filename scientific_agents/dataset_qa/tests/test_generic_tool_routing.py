"""Advertised tool inputs distinguish capabilities sharing one source name."""
from dataclasses import replace

import pytest

from ..mcp import Tool
from ..routing import select_tools


def catalogue():
    tools = []
    for name, group, title, properties in [
        ("lookup_catalogue", "catalogue", "ArchiveDB dataset search", {
            "dataset_identifier": {"type": "string", "description": "Collection identifiers"}}),
        ("match_structures", "molecules", "ArchiveDB molecular similarity", {
            "molecular_weight": {"type": "number", "description": "Mass interval"}}),
        ("transform_measurements", "cells", "ArchiveDB cell normalization", {
            "expression_matrix": {"type": "string", "description": "Transcript abundance measurements"},
            "method": {"type": "string", "enum": ["log_counts", "scaled_counts"]}}),
    ]:
        tools.append(Tool("shared-service", name, "Work with ArchiveDB records",
            {"type": "object", "properties": properties}, {"title": title},
            {"piflow": {"qa": {"routing": {"group": group, "source": "ArchiveDB"}}}}))
    return tools


@pytest.mark.parametrize("query,expected", [
    ("ArchiveDB molecular similarity", "match_structures"),
    ("ArchiveDB molecular weight", "match_structures"),
    ("ArchiveDB transcript abundance", "transform_measurements"),
    ("ArchiveDB scaled counts", "transform_measurements"),
])
def test_current_request_disambiguates_shared_source_using_advertised_inputs(query, expected):
    tools = catalogue()
    ranked = select_tools(tools, query, recent=[("shared-service", "lookup_catalogue")])
    assert ranked[0].name == expected
    assert set(tool.name for tool in ranked) == set(tool.name for tool in tools)


def test_history_breaks_only_equal_relevance_and_browsing_remains_stable():
    tools = catalogue()
    recent = [("shared-service", "transform_measurements")]
    assert select_tools(tools, "ArchiveDB", recent=recent)[0].name == "transform_measurements"
    assert select_tools(tools, "ArchiveDB molecular_weight", recent=recent)[0].name == "match_structures"
    assert select_tools(tools, "") == tools


def test_explicit_group_filters_even_when_other_group_matches_the_request():
    tools = catalogue()
    assert select_tools(tools, "ArchiveDB molecular weight", group="catalogue") == [tools[0]]
    assert select_tools(tools, "ArchiveDB", group="unknown") == []


def test_source_hint_keeps_other_sources_reachable():
    tools = catalogue()
    tools[2] = replace(tools[2], meta={"piflow": {"qa": {
        "routing": {"group": "cells", "source": "OtherArchive"}}}})
    ranked = select_tools(tools, "OtherArchive", recent=[("shared-service", "lookup_catalogue")])
    assert ranked[0] == tools[2]
    assert len(ranked) == 3
    assert select_tools(tools, "OtherArchive", group="catalogue") == [tools[0]]


def test_schema_vocabulary_needs_no_routing_metadata_and_ignores_example_data():
    decoy = Tool("service", "first", "Process records", {"type": "object", "properties": {
        "value": {"type": "string", "default": "rare lineage", "examples": ["rare lineage"]}}}, {}, {})
    target = Tool("service", "second", "Process records", {"type": "object", "properties": {
        "options": {"$ref": "#/$defs/Options"}}, "$defs": {"Options": {"type": "object", "properties": {
            "labels": {"type": "array", "items": {"anyOf": [
                {"type": "string", "enum": ["rare_lineage"]}, {"type": "null"}]}}}}}}, {}, {})
    assert select_tools([decoy, target], "rare lineage")[0] == target
    assert select_tools([decoy, target], "unmatched request") == [decoy, target]


def test_compatible_consumer_recall_preserves_leading_request_and_explicit_group():
    tools = catalogue()
    consumer = Tool("shared-service", "materialize", "Represent an owned resource",
        {"type": "object", "properties": {"source_ref": {"type": "string"}}}, {},
        {"piflow": {"qa": {"bind": {"source_ref": ["/source_ref"]},
            "artifact": {"consume": "source_ref"}, "routing": {"group": "conversion"}}}})
    tools.append(consumer)
    resource = {"server": "shared-service", "kind": "record_resource"}
    assert select_tools(tools, "ArchiveDB molecular weight", resources=[resource])[:2] == [tools[1], consumer]
    assert select_tools(tools, "ArchiveDB molecular weight", group="molecules", resources=[resource]) == [tools[1]]
    assert select_tools(tools, "ArchiveDB molecular weight", resources=[{**resource, "server": "other"}])[-1] == consumer
