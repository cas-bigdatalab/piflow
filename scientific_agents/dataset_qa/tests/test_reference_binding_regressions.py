"""Identity provenance, canonical pointers and source-aware reference recovery."""
from copy import deepcopy

import pytest

from ..capabilities import inputs
from ..context import encode, project, slice_result
from ..contracts import QAError
from ..references import at_path, matching_objects, preview
from .test_dataset_qa import Backend, Dialogue, engine, session
from .test_reference_recovery import bound_tool, reference
from .test_references import stored
from ..service import DatasetQA


@pytest.mark.parametrize("path", ["/items/01", "/items/\u00b2", "/items/\u0661", "/items/-", "/bad~2", "/bad~"])
@pytest.mark.parametrize("reader", [at_path, slice_result])
def test_noncanonical_or_invalid_pointer_never_resolves_another_value(path, reader):
    value = {"items": [{"id": "A"}, {"id": "B"}], "bad~2": "wrong", "bad~": "wrong"}
    with pytest.raises(QAError):
        reader(value, path)


def test_pointer_escape_order_and_object_numeric_keys_are_preserved():
    value = {"a/b": {"~key": [{"~1": {"01": "value"}}]}}
    pointer = "/a~1b/~0key/0/~01/01"
    assert at_path(value, pointer)=="value"
    assert slice_result(value, pointer)==("value", False)


@pytest.mark.parametrize("path", ["/password", "/nested/token", "/items/0/Authorization"])
def test_public_leaf_reads_cannot_bypass_sensitive_field_redaction(path):
    value = {"password": "hidden", "nested": {"token": "hidden"}, "items": [{"Authorization": "hidden"}]}
    with pytest.raises(QAError) as failure:
        slice_result(value, path)
    assert failure.value.code=="invalid_pointer" and failure.value.status==403
    # Source bindings remain a separate trusted operation; public projections
    # and reads may not expose their otherwise redacted fields.
    assert at_path(value, path)=="hidden"


def test_declared_binding_uses_only_lossless_schema_normalization():
    tool = bound_tool(binding={"asset_key": ["/id", "/raw/id"]})
    source = {"id": 42, "raw": {"id": "42"}}
    snapshot = deepcopy(source)
    assert inputs(tool, {"asset_key": 42}, source)=={"asset_key": "42"}
    assert source==snapshot
    numeric = bound_tool({"asset_key": {"type": "integer"}}, {"asset_key": ["/id"]})
    assert inputs(numeric, {}, {"id": "42"})=={"asset_key": 42}
    # Leading zeros can distinguish actual source identifiers.
    assert inputs(numeric, {}, {"id": "0042"})=={"asset_key": "0042"}
    assert inputs(tool, {}, {"id": True})=={"asset_key": True}


def test_binding_schema_normalization_resolves_local_schema_references():
    tool = bound_tool({"asset_key": {"$ref": "#/$defs/key"}}, {"asset_key": ["/id"]})
    tool.schema["$defs"] = {"key": {"type": "string", "pattern": "^[0-9]+$"}}
    assert inputs(tool, {}, {"id": 42})=={"asset_key": "42"}


@pytest.mark.parametrize("source,arguments", [
    ({"id": 1, "raw": {"id": True}}, {}),
    ({"id": 1}, {"asset_key": True}),
    ({"id": {"nested": 1}}, {"asset_key": {"nested": True}}),
])
def test_boolean_and_numeric_identities_never_compare_equal(source, arguments):
    tool = bound_tool({"asset_key": {}}, {"asset_key": ["/id", "/raw/id"]})
    with pytest.raises(QAError):
        inputs(tool, arguments, source)


@pytest.mark.parametrize("collection", ["items", "records"])
def test_nested_identity_resolves_the_complete_collection_record(collection):
    card = {"result_id": "source", "data": {collection: [
        {"identity": {"key": "asset-9", "owner": "tenant"}, "title": "Dataset"}]}}
    assert matching_objects(card, "asset-9")==[reference("source", "/"+collection+"/0")]


def test_candidate_preview_preserves_ordinals_through_nonrecord_rows():
    card = {"result_id": "source", "data": {"items": [None, {"id": "B"}, "note", {"id": "D"}]}}
    view = preview({"candidates": reference("source", "/items")}, {"source": card})["candidates"]
    assert [(item["handle"], item["path"]) for item in view["items"]]==[
        ("candidate:2", "/items/1"), ("candidate:4", "/items/3")]
    assert "next_offset" not in view


def test_context_projection_never_synthesizes_a_shortened_opaque_identifier():
    identifier = "opaque-key-"+"ab12"*120
    result, cut = project({"asset_reference": identifier, "description": "free text "*100}, 160)
    assert cut and len(encode(result))<=160
    assert "asset_reference" not in result or result["asset_reference"]==identifier
    # Natural prose in languages without word separators remains summarizable.
    result, cut = project({"description": "这份数据记录逐小时气象观测值。"*100}, 160)
    assert cut and result["description"].endswith("…")


def test_same_id_in_separate_relevant_sources_requires_disambiguation(engine):
    service = DatasetQA(engine, Dialogue(), Backend().gateway())
    sid = session(service)
    first = stored(service, sid, "source-a", {"items": [{"id": "same", "title": "A"}]})
    second = stored(service, sid, "source-b", {"items": [{"id": "same", "title": "B"}]})
    a, b = reference(first["result_id"], "/items/0"), reference(second["result_id"], "/items/0")
    assert service.store.object_reference("alice", sid, "same", [a, b])==[a, b]
    assert service.store.object_reference("alice", sid, "same", [a, b], first["result_id"])==[a]
    # Current focus and its containing list are one source record, not ambiguity.
    assert service.store.object_reference("alice", sid, "same", [a, reference(first["result_id"], "/items")])==[a]


def test_same_id_in_unscoped_history_does_not_silently_choose_the_newest(engine):
    service = DatasetQA(engine, Dialogue(), Backend().gateway())
    sid = session(service)
    first = stored(service, sid, "source-a", {"id": "same", "title": "A"})
    second = stored(service, sid, "source-b", {"id": "same", "title": "B"})
    assert {item["result_id"] for item in service.store.object_reference("alice", sid, "same")}=={
        first["result_id"], second["result_id"]}


def test_latest_displays_preserves_all_published_cards_and_their_order(engine):
    service = DatasetQA(engine, Dialogue(), Backend().gateway())
    sid = session(service)
    assert service.store.latest_displays("alice", sid)==[]
    first = stored(service, sid, "older", {"items": [{"id": "A"}]})
    second = stored(service, sid, "newer", {"items": [{"id": "B"}]})
    payload = {"message": "Show both", "params": {}, "parent_task_id": None,
        "delivery": [second["result_id"], first["result_id"]]}
    task, _ = service.store.submit("alice", sid, "combined", payload, None, service.owner)
    service.store.finish("alice", sid, task["id"], "COMPLETED", message="Both results")
    assert service.store.latest_displays("alice", sid)==[second, first]
    stored(service, sid, "unpublished", {"id": "not displayed"}, publish=False)
    assert service.store.latest_displays("alice", sid)==[second, first]
    with pytest.raises(QAError):
        service.store.latest_displays("other-user", sid)
