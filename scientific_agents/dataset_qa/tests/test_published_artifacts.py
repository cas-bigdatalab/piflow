"""Cross-turn file candidates come from actual delivery, not registration recency."""
from hashlib import sha256
import json
from types import SimpleNamespace

import pytest
from sqlalchemy import create_engine, delete, event
from sqlalchemy.pool import StaticPool

from ..artifacts import Artifacts, ArtifactSpec
from ..contracts import QAError
from ..persistence import Store


@pytest.fixture
def registry():
    engine = create_engine("sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False})
    try:
        yield Artifacts(Store(engine))
    finally:
        engine.dispose()


def begin(registry, request="first", user="alice"):
    store = registry.store
    sid = store.create(user, "", request)["id"]
    task, _ = store.submit(user, sid, request, {"message": "Find records"}, None, "worker")
    return sid, task["id"]


def save(registry, sid, tid, key, *, user="alice", name=None):
    card = {"result_id": tid+":"+str(key), "view_type": "table", "title": "Records", "data": {"resource": {
        "source_ref": "opaque-"+str(key), "format": "jsonl", "name": name or f"records-{key}.jsonl",
        "record_count": 1000, "sha256": sha256(str(key).encode()).hexdigest(), "fields": ["field"]}}}
    card["file_artifact"] = registry.register(user, sid, card,
        SimpleNamespace(server="records-service", name="query"), ArtifactSpec())
    registry.store.write(user, sid, tid, card=card)
    return card


def publish(registry, sid, tid, cards, *, lineage=None):
    payload = {"message": "Find records", "delivery": [card["result_id"] for card in cards]}
    if lineage:
        payload["delivery_lineage"] = lineage
    registry.store.write("alice", sid, tid, payload=payload)
    registry.store.finish("alice", sid, tid, "COMPLETED", message="Results ready")
    return registry.store.latest_displays("alice", sid)


def test_single_delivered_file_survives_reregistration_in_other_session(registry):
    sid, tid = begin(registry)
    source = save(registry, sid, tid, "same")
    cards = publish(registry, sid, tid, [source])
    other_sid, other_tid = begin(registry, "other")
    newer = save(registry, other_sid, other_tid, "same")
    assert newer["file_artifact"] == source["file_artifact"]
    context = Artifacts(registry.store).published("alice", sid, cards)
    assert context["total"] == 1
    assert context["items"][0]["handle"] == source["file_artifact"]
    assert context["items"][0]["result_id"] == source["result_id"]
    assert context["items"][0]["server"] == "records-service"
    assert context["items"][0]["record_count"] == 1000
    assert "source_ref" not in json.dumps(context)
    assert "opaque-same" not in json.dumps(context)


def test_multiple_delivery_preserves_order_and_excludes_auxiliary_files(registry):
    sid, tid = begin(registry)
    first = save(registry, sid, tid, "first")
    auxiliary = save(registry, sid, tid, "auxiliary")
    second = save(registry, sid, tid, "second")
    cards = publish(registry, sid, tid, [second, first])
    context = registry.published("alice", sid, cards)
    assert context["total"] == 2
    assert [item["handle"] for item in context["items"]] == [second["file_artifact"], first["file_artifact"]]
    assert auxiliary["file_artifact"] not in json.dumps(context)


def test_merged_delivery_uses_saved_lineage_not_other_successful_results(registry):
    sid, tid = begin(registry)
    first = save(registry, sid, tid, "first")
    second = save(registry, sid, tid, "second")
    auxiliary = save(registry, sid, tid, "auxiliary")
    combined = {"result_id": tid+":delivery", "view_type": "table", "title": "Combined",
        "data": [second["data"], first["data"]]}
    registry.store.write("alice", sid, tid, card=combined)
    cards = publish(registry, sid, tid, [combined], lineage={combined["result_id"]: {
        "0": {"result_id": second["result_id"], "path": ""},
        "1": {"result_id": first["result_id"], "path": ""}}})
    context = registry.published("alice", sid, cards)
    assert [item["result_id"] for item in context["items"]] == [second["result_id"], first["result_id"]]
    assert {item["display_result_id"] for item in context["items"]} == {combined["result_id"]}
    assert auxiliary["file_artifact"] not in json.dumps(context)


def test_published_files_are_bounded_without_truncating_identifiers_or_n_plus_one_queries(registry):
    sid, tid = begin(registry)
    cards = [save(registry, sid, tid, i, name="large"*1000) for i in range(30)]
    cards = publish(registry, sid, tid, cards)
    statements = []
    def capture(conn, cursor, statement, parameters, context, executemany):
        statements.append(statement)
    event.listen(registry.store.engine, "before_cursor_execute", capture)
    try:
        context = registry.published("alice", sid, cards, limit=1300)
    finally:
        event.remove(registry.store.engine, "before_cursor_execute", capture)
    assert context["total"] == 30 and context["truncated"]
    assert 0 < len(context["items"]) < 30
    assert len(json.dumps(context, ensure_ascii=False, sort_keys=True, separators=(",", ":"))) <= 1300
    assert all(item["handle"] == card["file_artifact"] and item["result_id"] == card["result_id"]
        for item, card in zip(context["items"], cards))
    assert len(statements) == 2  # Session ownership and one batched manifest lookup.


def test_merged_lineage_preserves_numeric_display_order_after_json_storage(registry):
    sid, tid = begin(registry)
    originals = [save(registry, sid, tid, index) for index in range(12)]
    combined = {"result_id": tid+":delivery", "data": [card["data"] for card in originals]}
    registry.store.write("alice", sid, tid, card=combined)
    cards = publish(registry, sid, tid, [combined], lineage={combined["result_id"]: {
        str(index): {"result_id": card["result_id"], "path": ""} for index, card in enumerate(originals)}})
    context = registry.published("alice", sid, cards, limit=8000)
    assert [item["result_id"] for item in context["items"]] == [card["result_id"] for card in originals]


def test_tiny_manifest_budget_reports_omission_without_partial_handle(registry):
    sid, tid = begin(registry)
    source = save(registry, sid, tid, "source")
    cards = publish(registry, sid, tid, [source])
    context = registry.published("alice", sid, cards, limit=128)
    assert context == {"items": [], "total": 1, "truncated": True}


def test_absent_artifact_is_not_silently_replaced_by_recent_file(registry):
    sid, tid = begin(registry)
    card = save(registry, sid, tid, "missing")
    cards = publish(registry, sid, tid, [card])
    with registry.store.transaction() as conn:
        conn.execute(delete(registry.table).where(registry.table.c.id == card["file_artifact"]))
    other_sid, other_tid = begin(registry, "other")
    save(registry, other_sid, other_tid, "unrelated")
    context = registry.published("alice", sid, cards)
    assert context["items"] == [] and context["unavailable"] == context["total"] == 1


def test_published_context_checks_session_ownership_and_skips_non_files(registry):
    sid, tid = begin(registry)
    card = {"result_id": tid+":text", "data": {"description": "No file artifact"}}
    registry.store.write("alice", sid, tid, card=card)
    cards = publish(registry, sid, tid, [card])
    assert registry.published("alice", sid, cards) == {}
    with pytest.raises(QAError) as caught:
        registry.published("bob", sid, cards)
    assert caught.value.code == "session_not_found"
