"""Interruption publishes only committed, necessary evidence in one transaction."""
from copy import deepcopy
import json

import pytest
from sqlalchemy import update

from ..operations import Operations
from ..persistence import Store
from .test_dataset_qa import engine, result_cards


@pytest.mark.parametrize("ending", ["cancel", "lease"])
@pytest.mark.parametrize("selection", ["automatic", "explicit", "empty"])
def test_interruption_preserves_selection_and_filters_auxiliary_unconfirmed_missing_and_foreign_results(engine, ending, selection):
    store = Store(engine)
    sid = store.create("alice", "", "session")["id"]
    payload = {"message": "Prepare the requested datasets", "params": {}}
    task, _ = store.submit("alice", sid, "request", payload, None, "old-worker")
    tid = task["id"]
    operations = Operations()
    capability = {"server": "data", "name": "query"}
    for description, result_id, required in (("Requested", "good", True),
            ("Supporting", "auxiliary", False), ("Unconfirmed", "candidate", False),
            ("Missing artifact", "missing", True), ("Foreign artifact", "foreign", True)):
        key = operations.register(description, capability, planned=required, required=required)
        if description=="Unconfirmed":
            operations.get(key)["inferred"] = True
        operations.start(key, description, capability, retry_safe=True)
        operations.finish(key, description, result_id=result_id)
    waiting = operations.register("Still waiting", {"server": "data", "name": "inspect"}, planned=True)
    operations.start(waiting, "in-flight", capability, retry_safe=True)
    payload["operations"] = operations.items
    if selection!="automatic":
        payload["delivery"] = ["good"] if selection=="explicit" else []
        payload["delivery_sources"] = list(payload["delivery"])
    store.write("alice", sid, tid, payload=payload)
    for result_id in ("good", "auxiliary", "candidate"):
        store.write("alice", sid, tid, card={"result_id": result_id, "view_type": "data",
            "title": result_id, "data": {"items": [{"id": result_id}]}})
    other_sid = store.create("alice", "", "other-session")["id"]
    other, _ = store.submit("alice", other_sid, "other", {"message": "Other dataset"}, None, "other-worker")
    store.write("alice", other_sid, other["id"], card={"result_id": "foreign", "view_type": "data",
        "title": "Foreign", "data": {"items": [{"id": "foreign"}]}})
    receipts = deepcopy(operations.items)
    if ending=="cancel":
        assert store.finish("alice", sid, tid, "CANCELLED")
    else:
        with store.transaction() as conn:
            conn.execute(update(store.tasks).where(store.tasks.c.id==tid).values(expires=0))
        store.heartbeat("new-worker", [])
    ledger = json.loads(store.task("alice", sid, tid)["payload"])
    assert ledger["operations"][:-1]==receipts[:-1]
    assert ledger["operations"][-1]["state"]=="unknown"
    assert ledger["operations"][-1]["attempts"][0]["state"]=="unknown"
    assert ledger["operations"][-1]["attempts"][0]["error"]["code"]=="execution_unknown"
    events = store.replay("alice", sid, tid, 0)
    expected = [] if selection=="empty" else ["good"]
    assert [card["result_id"] for card in result_cards(events)]==expected
    assert ledger["delivery"]==ledger["delivery_sources"]==expected
    assert events[-1]["status"]==("CANCELLED" if ending=="cancel" else "FAILED")
    assert not store.finish("alice", sid, tid, "COMPLETED")
    assert not store.write("alice", sid, tid, card={"result_id": "late", "title": "Late", "view_type": "data", "data": []})
    assert store.replay("alice", sid, tid, 0)==events


def test_legacy_task_without_operation_proof_does_not_publish_raw_results_on_cancel(engine):
    store = Store(engine)
    sid = store.create("alice", "", "legacy")["id"]
    task, _ = store.submit("alice", sid, "request", {"message": "Continue"}, None, "worker")
    store.write("alice", sid, task["id"], card={"result_id": "legacy-raw", "title": "Unconfirmed",
        "view_type": "data", "data": []})
    assert store.finish("alice", sid, task["id"], "CANCELLED")
    assert not result_cards(store.replay("alice", sid, task["id"], 0))
    assert "operations" not in json.loads(store.task("alice", sid, task["id"])["payload"])
