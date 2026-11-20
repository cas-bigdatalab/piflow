"""Reuse exposes complete saved criteria, field scope and actual producing tools."""
import asyncio
from copy import deepcopy
from hashlib import sha256
import json
from types import SimpleNamespace

import pytest
from sqlalchemy import event

from ..artifacts import ArtifactSpec
from ..dialogue import Read
from ..service import DatasetQA
from .test_published_artifacts import begin, publish, registry


def save(registry, sid, tid, key, *, query, fields=None, parent=None, tool="read_measurements", user="alice"):
    resource = {"source_ref": "private-source-"+key, "format": "csv" if parent else "jsonl",
        "name": key+".csv", "record_count": 250, "fields": fields or ["time", "value"],
        "sha256": sha256(key.encode()).hexdigest()}
    data = {"resource": resource, "record_count": 250, "query": deepcopy(query)}
    if parent:
        data["parent_source_ref"] = parent
    card = {"result_id": tid+":"+key, "data": data, "view_type": "url", "title": "Measurements"}
    card["file_artifact"] = registry.register(user, sid, card,
        SimpleNamespace(server="arbitrary-records", name=tool), ArtifactSpec())
    registry.store.write(user, sid, tid, card=card)
    return card


def test_export_published_context_retains_original_criteria_and_both_producers(registry):
    sid, tid = begin(registry)
    query = {"station": "station-a", "window": [0, 10], "limit": 250, "columns": ["time", "value"]}
    source = save(registry, sid, tid, "source", query=query)
    exported = save(registry, sid, tid, "export", query=query,
        parent=source["data"]["resource"]["source_ref"], tool="write_file")
    cards = publish(registry, sid, tid, [exported])
    statements = []
    def capture(conn, cursor, statement, parameters, context, executemany):
        statements.append(statement)
    event.listen(registry.store.engine, "before_cursor_execute", capture)
    try:
        context = registry.published("alice", sid, cards)
    finally:
        event.remove(registry.store.engine, "before_cursor_execute", capture)
    item = context["items"][0]
    assert item["tool"] == "write_file"
    assert item["source_producer"] == {"server": "arbitrary-records", "tool": "read_measurements"}
    assert item["criteria"] == query and item["record_count"] == 250
    assert item["fields"] == ["time", "value"]
    assert not any(key.endswith("_omitted") for key in item)
    assert len(statements) == 3  # One batched source-manifest lookup, never per candidate.
    serialized = json.dumps(context)
    assert "source_ref" not in serialized and "private-source-" not in serialized
    assert "format-only" in context["guidance"]
    assert "Changed requirements" in context["guidance"]
    assert "format-only export, which preserves selection, count and field scope" in context["guidance"]


@pytest.mark.parametrize("merged", [False, True], ids=["direct", "merged"])
def test_large_criteria_are_omitted_whole_with_an_exact_saved_result_pointer(registry, merged):
    sid, tid = begin(registry)
    query = {"region": "original-region", "conditions": ["complete-condition-"+str(i)+"x"*70 for i in range(40)]}
    source = save(registry, sid, tid, "large", query=query)
    if merged:
        combined = {"result_id": tid+":delivery", "view_type": "table", "title": "Combined",
            "data": [source["data"]]}
        registry.store.write("alice", sid, tid, card=combined)
        cards = publish(registry, sid, tid, [combined], lineage={combined["result_id"]: {
            "0": {"result_id": source["result_id"], "path": ""}}})
    else:
        cards = publish(registry, sid, tid, [source])
    context = registry.published("alice", sid, cards, limit=1800)
    item = context["items"][0]
    assert "criteria" not in item and item["criteria_omitted"] is True
    assert item["criteria_path"] == "/query" and item["result_id"] == source["result_id"]
    if merged:
        assert item["display_result_id"] == combined["result_id"] != item["result_id"]
    service = SimpleNamespace(store=registry.store, gateway=SimpleNamespace(limits=SimpleNamespace(result_chars=8000)))
    saved = asyncio.run(DatasetQA._read_result(service, "alice", sid,
        Read(result_id=item["result_id"], path=item["criteria_path"])))
    assert saved["data"] == query
    assert len(json.dumps(context, ensure_ascii=False, sort_keys=True, separators=(",", ":"))) <= 1800
    catalogue = registry.find("alice", query=source["file_artifact"])["items"][0]
    assert "criteria" not in catalogue and catalogue["criteria_omitted"] and catalogue["truncated"]


def test_large_field_scope_is_never_presented_as_a_complete_shortened_list(registry):
    sid, tid = begin(registry)
    fields = ["full_field_name_"+str(i)+"x"*60 for i in range(50)]
    source = save(registry, sid, tid, "many-fields", query={"partition": "east"}, fields=fields)
    context = registry.published("alice", sid, publish(registry, sid, tid, [source]))
    item = context["items"][0]
    assert item["criteria"] == {"partition": "east"}
    assert "fields" not in item and item["fields_omitted"] is True
    assert item["fields_path"] == "/resource/fields"
    assert item["record_count"] == 250


def test_sanitized_criteria_do_not_look_like_complete_original_conditions(registry):
    sid, tid = begin(registry)
    source = save(registry, sid, tid, "sensitive", query={"threshold": 0.5, "api_key": "test-secret-do-not-expose"})
    context = registry.published("alice", sid, publish(registry, sid, tid, [source]))
    item = context["items"][0]
    assert "criteria" not in item and item["criteria_omitted"]
    assert "test-secret-do-not-expose" not in json.dumps(context)
    catalogue = registry.find("alice")["items"][0]
    assert "criteria" not in catalogue and catalogue["criteria_omitted"]


def test_source_producer_lookup_never_uses_another_users_manifest(registry):
    other_sid, other_tid = begin(registry, "other", user="bob")
    foreign = save(registry, other_sid, other_tid, "foreign", query={"partition": "private"}, user="bob")
    sid, tid = begin(registry)
    exported = save(registry, sid, tid, "unresolved-parent", query={"partition": "public"},
        parent=foreign["data"]["resource"]["source_ref"], tool="write_file")
    context = registry.published("alice", sid, publish(registry, sid, tid, [exported]))
    assert "source_producer" not in context["items"][0]
    assert context["items"][0]["criteria"] == {"partition": "public"}
