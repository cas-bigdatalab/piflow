"""Source-backed names survive bounded evidence and tool-free recovery."""
from copy import deepcopy

from ..context import project
from ..operations import Operations
from ..references import compact_record, record_name
from ..responses import recovery_search_summary


def test_bounded_record_preserves_supplied_name_without_renaming_wire_fields():
    record = {"Description": "observation " * 300, "Name": "Source record", "UID": 17}
    original = deepcopy(record)
    assert project(record, 80)[0]["Name"] == "Source record"
    assert compact_record(record, 80)["Name"] == "Source record"
    assert record_name(record) == "Source record"
    assert record == original


def test_declared_name_cannot_be_replaced_by_provider_or_other_label():
    record = {"label": "Provider", "metadata": {"designation": "Actual specimen"}}
    assert record_name(record, ["/metadata/designation"]) == "Actual specimen"
    assert record_name(record, ["/missing"]) is None
    assert record_name({"id": "R-1", "source": "Provider"}) is None


def test_name_declaration_cannot_publish_redacted_fields():
    record = {"Name": "Visible", "TOKEN": "hidden", "metadata": {"Password": "hidden"}}
    assert record_name(record, ["/TOKEN", "/metadata/Password"]) is None
    assert record_name(record, ["/TOKEN", "/Name"]) == "Visible"


def test_recovery_keeps_cross_database_ids_and_declared_names_without_a_model():
    rows = [
        {"db": "one", "id": "shared", "metadata": {"designation": "First specimen"}},
        {"db": "two", "id": "shared", "metadata": {"designation": "Second specimen"}},
    ]
    operations = Operations([{
        "id": "op1", "description": "Find specimens", "state": "succeeded", "required": True,
        "attempts": [{"state": "succeeded", "key": "call1", "result_id": "result1",
            "presentation": {"kind": "collection", "path": "/results", "name_paths": ["/metadata/designation"]}}],
        "search": {"profile": {"query": "term", "identity": ["/db", "/id"], "identity_mode": "composite"},
            "done": True, "stop": "exhausted", "records": ["one", "two"]},
    }])
    cards = [{"result_id": "result1", "title": "Tool card title", "data": {"results": rows}}]
    reply = recovery_search_summary(operations, cards, resource_noun="记录")
    assert "2 个候选记录" in reply
    assert "First specimen" in reply and "Second specimen" in reply
    assert "Tool card title" not in reply
