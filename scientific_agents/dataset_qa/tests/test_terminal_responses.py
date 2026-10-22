"""Terminal replies survive worker loss without changing execution receipts."""
import json

import pytest
from sqlalchemy import update

from ..persistence import Store
from ..responses import terminal_reply
from .test_dataset_qa import engine


def started(engine):
    store = Store(engine)
    sid = store.create("alice", "", "terminal-session")["id"]
    task, _ = store.submit("alice", sid, "turn", {"message": "查看数据", "params": {}}, None, "worker")
    return store, sid, task["id"]


def replies(store, sid, tid):
    events = store.replay("alice", sid, tid, 0)
    text = ""
    for value in events:
        if value["type"] == "message":
            text = value["text"] if value.get("mode") == "replace" else text+value["text"]
    rows, _ = store.history("alice", sid)
    saved = [json.loads(row["payload"])["text"] for row in rows
        if row["task_id"] == tid and row["kind"] == "ASSISTANT_MESSAGE"]
    return events, text, saved


@pytest.mark.parametrize("status", ["FAILED", "CANCELLED", "COMPLETED"])
def test_empty_terminal_reply_is_published_persisted_and_idempotent(engine, status):
    store, sid, tid = started(engine)
    error = {"code": 502, "error_code": "tool_failed", "message": "SECRET /private/root"} if status == "FAILED" else None
    assert store.finish("alice", sid, tid, status, error=error)
    events, text, saved = replies(store, sid, tid)
    assert text.strip() and saved == [text]
    assert text == terminal_reply(status, error=error)
    assert events[-1]["status"] == status
    assert "SECRET" not in text and "/private/root" not in text
    assert store.session("alice", sid)["active_task_id"] is None
    assert not store.finish("alice", sid, tid, status, error=error)
    assert replies(store, sid, tid) == (events, text, saved)


@pytest.mark.parametrize("status", ["FAILED", "CANCELLED", "COMPLETED"])
@pytest.mark.parametrize("supplied", [False, True])
def test_committed_partial_text_is_not_lost_or_streamed_twice(engine, status, supplied):
    store, sid, tid = started(engine)
    first, second = "已经确认的数据：", "已有两条记录。"
    store.write("alice", sid, tid, {"type": "message", "text": first})
    store.write("alice", sid, tid, {"type": "message", "text": second})
    complete = first+second
    error = {"code": 504, "error_code": "execution_unknown", "message": "worker traceback"} if status == "FAILED" else None
    assert store.finish("alice", sid, tid, status, message=complete if supplied else "", error=error)
    events, text, saved = replies(store, sid, tid)
    assert text.startswith(complete) and text.count(complete) == 1
    assert saved == [text]
    if status == "CANCELLED" or (status == "FAILED" and not supplied):
        assert text == complete+"\n\n"+terminal_reply(status, error=error)
        assert len([value for value in events if value["type"] == "message"]) == 3
    else:
        assert text == complete
        assert len([value for value in events if value["type"] == "message"]) == 2


def test_finish_publishes_only_the_unflushed_text_suffix(engine):
    store, sid, tid = started(engine)
    store.write("alice", sid, tid, {"type": "message", "text": "已获取"})
    assert store.finish("alice", sid, tid, "COMPLETED", message="已获取相关数据。")
    events, text, saved = replies(store, sid, tid)
    assert [value["text"] for value in events if value["type"] == "message"] == ["已获取", "相关数据。"]
    assert saved == [text] == ["已获取相关数据。"]


@pytest.mark.parametrize("status", ["FAILED", "CANCELLED", "COMPLETED"])
def test_conflicting_worker_text_preserves_the_committed_reply(engine, status):
    store, sid, tid = started(engine)
    committed = "已经确认的内容保留。"
    store.write("alice", sid, tid, {"type": "message", "text": committed})
    assert store.finish("alice", sid, tid, status, message="过时的工作线程答复")
    events, text, saved = replies(store, sid, tid)
    assert saved == [text] == [committed+"\n\n"+terminal_reply(status)]
    assert "过时的工作线程答复" not in text
    assert all(value.get("mode") != "replace" for value in events)
    assert text.count(committed) == 1


@pytest.mark.parametrize("partial", ["", "已经确认一项信息。"])
def test_lease_expiry_has_a_persisted_reply_without_worker_or_model(engine, partial):
    store, sid, tid = started(engine)
    if partial:
        store.write("alice", sid, tid, {"type": "message", "text": partial})
    with store.transaction() as conn:
        conn.execute(update(store.tasks).where(store.tasks.c.id == tid).values(expires=0))
    store.heartbeat("replacement-worker", [])
    events, text, saved = replies(store, sid, tid)
    assert text.strip() and saved == [text]
    assert text.startswith(partial)
    assert events[-1]["status"] == "FAILED" and events[-1]["code"] == "execution_unknown"
    assert not store.write("alice", sid, tid, {"type": "message", "text": "late reply"})
    store.heartbeat("replacement-worker", [])
    assert replies(store, sid, tid) == (events, text, saved)


def test_cancel_waiting_turn_updates_one_assistant_message(engine):
    store, sid, tid = started(engine)
    question = "请选定需要查看的数据集。"
    store.write("alice", sid, tid, {"type": "message", "text": question})
    assert store.finish("alice", sid, tid, "WAITING_INPUT", message=question)
    previous_events, _, _ = replies(store, sid, tid)
    assert store.finish("alice", sid, tid, "CANCELLED")
    events, text, saved = replies(store, sid, tid)
    assert saved == [text] == [question+"\n\n"+terminal_reply("CANCELLED")]
    tail = store.replay("alice", sid, tid, previous_events[-1]["event_seq"])
    assert [value["type"] for value in tail] == ["message", "done"]
    assert tail[0]["text"] == "\n\n"+terminal_reply("CANCELLED")
    assert events[-1]["status"] == "CANCELLED"


def test_backend_error_text_is_never_used_as_a_terminal_message(engine):
    store, sid, tid = started(engine)
    error = {"code": 502, "error_code": "tool_failed", "message": "SECRET root /home/service/db",
        "detail": {"diagnostic": "internal trace"}}
    assert store.finish("alice", sid, tid, "FAILED", error=error)
    events, text, saved = replies(store, sid, tid)
    payload = json.loads(store.task("alice", sid, tid)["payload"])
    assert payload["error"]["error_code"] == "tool_failed"
    assert payload["error"]["detail"] == error["detail"]
    assert payload["error"]["message"] == events[-1]["message"] == text
    assert saved == [text] and "SECRET" not in text and "internal trace" not in text
    assert error["message"].startswith("SECRET")  # The caller's diagnostics are not mutated.


def test_response_and_terminal_event_commit_atomically(engine, monkeypatch):
    store, sid, tid = started(engine)
    original = store._event

    def interrupted(conn, task_id, data):
        if data["type"] == "done":
            raise RuntimeError("simulated transaction interruption")
        return original(conn, task_id, data)

    monkeypatch.setattr(store, "_event", interrupted)
    with pytest.raises(RuntimeError, match="transaction interruption"):
        store.finish("alice", sid, tid, "CANCELLED")
    assert store.task("alice", sid, tid)["status"] == "RUNNING"
    assert replies(store, sid, tid) == ([], "", [])
    monkeypatch.setattr(store, "_event", original)
    assert store.finish("alice", sid, tid, "CANCELLED")
    events, text, saved = replies(store, sid, tid)
    assert saved == [text] and [value["type"] for value in events] == ["message", "done"]
