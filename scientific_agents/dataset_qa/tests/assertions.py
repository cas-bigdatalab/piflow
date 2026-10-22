"""Verify friendly public outcomes without weakening execution-state checks."""
import json


def assert_completed(service, sid, event):
    """Successful-work tests must not pass through a partial public outcome."""
    assert event["type"] == "done"
    assert event["status"] == "COMPLETED", event
    assert "outcome" not in event and "code" not in event and "error_message" not in event
    sid = sid or service.store.task_session("alice", event["task_id"])
    task = service.store.task("alice", sid, event["task_id"])
    assert task["status"] == "COMPLETED"
    assert "error" not in json.loads(task["payload"])
    view = service.task_view(task)
    assert view["status"] == "COMPLETED" and "outcome" not in view and "error_message" not in view
    return task


def assert_handled(service, sid, event, code=None):
    """A completed reply can truthfully accompany an incomplete operation."""
    assert event["type"] == "done"
    assert event["status"] == "COMPLETED"
    assert event["outcome"] in {"partial", "unavailable"}
    assert "code" not in event and "error_message" not in event
    assert event.get("message")
    sid = sid or service.store.task_session("alice", event["task_id"])
    task = service.store.task("alice", sid, event["task_id"])
    assert task["status"] == "FAILED"
    error = json.loads(task["payload"])["error"]
    if code is not None:
        assert error["error_code"] == code
    view = service.task_view(task)
    assert view["status"] == "COMPLETED" and view["outcome"] == event["outcome"]
    assert "code" not in view and "error_message" not in view
    return task
