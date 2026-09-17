"""Unified projections use native task state and retain the XDC paging contract."""
import asyncio
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from sqlalchemy import Column, MetaData, String, Table, Text, create_engine, insert, text
from sqlalchemy.pool import StaticPool

from scientific_agents.forecast.persistence import session_key
from scientific_agents.forecast.sessions import HostSessions
from scientific_agents.unified.adapters.forecast import BASE, ForecastAdapter


@pytest.fixture
def engine():
    db = create_engine("sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False})
    yield db
    db.dispose()


@pytest.mark.parametrize("total,page,count", [(0, 1, 0), (45, 2, 2), (45, 4, 0)])
def test_forecast_list_keeps_both_pagination_shapes_and_task_summaries(engine, total, page, count):
    table = Table("forecast_tasks", MetaData(), Column("run_id", String), Column("session", String),
                  Column("status", String), Column("payload", Text), Column("updated_at", String))
    table.create(engine)
    with engine.begin() as conn:
        conn.execute(insert(table), [
            {"run_id": "old", "session": session_key("user", "s-0"), "status": "failed",
             "payload": '{}', "updated_at": "2026-09-15"},
            {"run_id": "new", "session": session_key("user", "s-0"), "status": "completed",
             "payload": '{"stage":"report"}', "updated_at": "2026-09-16"},
            {"run_id": "private", "session": session_key("another-user", "s-0"), "status": "running",
             "payload": '{}', "updated_at": "2026-09-17"},
        ])
    data = {"sessions": [{"session_id": f"s-{i}", "title": f"Session {i}"} for i in range(count)],
            "total": total, "pageNum": page, "pageSize": 20}
    before = deepcopy(data)
    native = SimpleNamespace(user="user", json=AsyncMock(return_value=data),
                             extension=SimpleNamespace(store=SimpleNamespace(engine=engine, tasks=table)))
    result = asyncio.run(ForecastAdapter(native).list_sessions(page, 20))
    expected = {"total": total, "pageNum": page, "pageSize": 20}
    assert result["pagination"] == expected
    assert {key: result[key] for key in expected} == expected
    assert len(result["items"]) == count
    if count:
        assert result["items"][0]["task_count"] == 2
        assert result["items"][0]["latest_task_id"] == "new"
        assert result["items"][0]["latest_task_status"] == "COMPLETED"
        assert result["items"][1]["task_count"] == 0
    native.json.assert_awaited_once_with("GET", BASE + "/sessions", query={"pageNum": page, "pageSize": 20})
    assert data == before


@pytest.mark.parametrize("task_state,available,item_state,result_state", [
    ("completed", True, "completed", "ready"),
    ("completed", None, "completed", "ready"),
    ("completed", False, "completed", "unavailable"),
    ("failed", False, "failed", "failed"),
    ("cancelled", False, "cancelled", "cancelled"),
    ("interrupted", False, "failed", "failed"),
    ("running", False, "running", "running"),
    (None, None, "unknown", "unknown"),
])
def test_restored_result_reflects_task_state_and_preserves_messages(task_state, available, item_state, result_state):
    created = "2026-09-16T02:30:00+00:00"
    messages = [{"id": i, "reply_id": f"reply-{i}", "role": role, "content": content, "create_time": created}
                for i, role, content in [(1, "user", "Forecast temperature"), (2, "assistant", "Checking data"),
                                         (3, "assistant", "Stored task outcome")]]
    messages[-1]["run_id"] = "run-1"
    tasks = ([{"run_id": "run-1", "status": task_state, "result_available": available}]
             if task_state else [])
    data = {"session_id": "s-1", "messages": messages, "tasks": tasks, "view": {"interaction": None},
            "next_after": 3, "has_more": False}
    before = deepcopy(data)
    result = asyncio.run(ForecastAdapter(SimpleNamespace(json=AsyncMock(return_value=data))).get_session("s-1", 0, 100))
    assert [row["item_type"] for row in result["items"]] == ["USER_MESSAGE", "ASSISTANT_MESSAGE", "RESULT_CARD"]
    assert [row["create_time"] for row in result["items"]] == [created] * 3
    assert result["items"][0]["payload"]["text"] == messages[0]["content"]
    assert result["items"][1]["payload"]["text"] == messages[1]["content"]
    card = result["items"][-1]
    assert card["item_status"] == item_state
    assert card["payload"]["status"] == result_state
    assert card["payload"]["data"]["summary"] == messages[-1]["content"]
    assert result["next_after_item_id"] == 3
    assert not result["has_more"]
    assert data == before


def test_native_history_reads_existing_timestamp_without_changing_paging_or_scope(engine):
    with engine.begin() as conn:
        conn.execute(text("CREATE TABLE messages (id INTEGER PRIMARY KEY, role TEXT, content TEXT, created_at TIMESTAMP)"))
        conn.execute(text("CREATE TABLE forecast_message_deliveries (message_id INTEGER, session TEXT, key TEXT)"))
        for i, owner in [(1, "user"), (2, "user"), (3, "other-user")]:
            conn.execute(text("INSERT INTO messages VALUES (:id, 'assistant', 'Stored content', '2026-09-16 02:30:00')"), {"id": i})
            conn.execute(text("INSERT INTO forecast_message_deliveries VALUES (:id, :session, :key)"),
                         {"id": i, "session": session_key(owner, "s-1"), "key": f"run-{i}:result"})
    host = HostSessions.__new__(HostSessions)
    host.store = SimpleNamespace(engine=engine)
    host.sync = Mock()
    messages = host.history("user", "s-1", after=1, limit=1)
    assert messages == [{"id": 2, "role": "assistant", "content": "Stored content",
                         "reply_id": "result-run-2", "run_id": "run-2", "create_time": "2026-09-16T02:30:00+00:00"}]
    assert host.history("user", "s-1", after=2) == []
    host.sync.assert_called_with(session_key("user", "s-1"))


def test_postgres_history_resolves_database_zone_before_serializing():
    conn = Mock()
    conn.execute.return_value.mappings.return_value.all.return_value = [
        {"id": 1, "role": "assistant", "content": "Outcome", "delivery_key": "run-1:result",
         "created_at": datetime(2026, 9, 16, 10, 30, tzinfo=timezone(timedelta(hours=8)))}]
    engine = Mock()
    engine.dialect.name = "postgresql"
    engine.connect.return_value.__enter__ = Mock(return_value=conn)
    engine.connect.return_value.__exit__ = Mock(return_value=False)
    host = HostSessions.__new__(HostSessions)
    host.store = SimpleNamespace(engine=engine)
    host.sync = Mock()
    assert host.history("user", "s-1")[0]["create_time"] == "2026-09-16T02:30:00+00:00"
    assert "m.created_at AT TIME ZONE current_setting('TimeZone') AS created_at" in str(conn.execute.call_args.args[0])
