"""Small durable task/event store; SQLite locally, PostgreSQL when integrated."""
from contextlib import ExitStack
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import json
import sqlite3
import threading

from sqlalchemy import Column, Integer, MetaData, String, Table, Text, create_engine, insert, select, update


def session_key(user: str, thread: str, agent: str = "forecast") -> str:
    return sha256(json.dumps([user, thread, agent]).encode()).hexdigest()


class Store:
    def __init__(self, url: str):
        self.engine = create_engine(url, pool_pre_ping=True,
                                    connect_args={"check_same_thread": False, "timeout": 30} if url.startswith("sqlite") else {})
        meta = MetaData()
        self.tasks = Table("forecast_tasks", meta,
            Column("run_id", String(64), primary_key=True), Column("session", String(64), index=True),
            Column("status", String(32)), Column("payload", Text), Column("updated_at", String(40)))
        self.turns = Table("forecast_turns", meta,
            Column("id", String(64), primary_key=True), Column("session", String(64), index=True),
            Column("payload", Text))
        self.events = Table("forecast_events", meta,
            Column("id", Integer, primary_key=True, autoincrement=True),
            Column("session", String(64), index=True), Column("payload", Text))
        self.bindings = Table("forecast_bindings", meta,
            Column("session", String(64), primary_key=True), Column("agent", String(80)))
        meta.create_all(self.engine)
        self._lock = threading.RLock()

    def task(self, run_id: str, session: str | None = None):
        query = select(self.tasks).where(self.tasks.c.run_id == run_id)
        if session:
            query = query.where(self.tasks.c.session == session)
        with self.engine.connect() as conn:
            row = conn.execute(query).mappings().first()
        if row is None:
            return None
        return {**json.loads(row["payload"]), "run_id": row["run_id"], "status": row["status"],
                "session": row["session"], "updated_at": row["updated_at"]}

    def put_task(self, run_id: str, session: str, status: str, **payload):
        with self._lock, self.engine.begin() as conn:
            previous = conn.execute(select(self.tasks).where(self.tasks.c.run_id == run_id)).mappings().first()
            if previous and previous["session"] != session:
                raise ValueError("任务归属不一致")
            data = {**(json.loads(previous["payload"]) if previous else {}), **payload}
            if not previous:
                data.setdefault("created_at", datetime.now(timezone.utc).isoformat())
            values = dict(status=status, payload=json.dumps(data, ensure_ascii=False, allow_nan=False),
                          updated_at=datetime.now(timezone.utc).isoformat())
            if previous:
                conn.execute(update(self.tasks).where(self.tasks.c.run_id == run_id).values(**values))
            else:
                conn.execute(insert(self.tasks).values(run_id=run_id, session=session, **values))

    def list_tasks(self, session: str | None = None):
        query = select(self.tasks.c.run_id).order_by(self.tasks.c.updated_at.desc())
        if session:
            query = query.where(self.tasks.c.session == session)
        with self.engine.connect() as conn:
            ids = conn.execute(query).scalars().all()
        return [self.task(i) for i in ids]

    def turn(self, turn_id: str):
        with self.engine.connect() as conn:
            value = conn.execute(select(self.turns.c.payload).where(self.turns.c.id == turn_id)).scalar()
        return json.loads(value) if value else None

    def save_turn(self, turn_id: str, session: str, payload: dict):
        payload = {**payload, "created_at": datetime.now(timezone.utc).isoformat()}
        with self.engine.begin() as conn:
            conn.execute(insert(self.turns).values(id=turn_id, session=session,
                         payload=json.dumps(payload, ensure_ascii=False, allow_nan=False)))

    def list_turns(self, session: str):
        with self.engine.connect() as conn:
            rows = conn.execute(select(self.turns).where(self.turns.c.session == session)).mappings().all()
        return sorted([{"id": r["id"], **json.loads(r["payload"])} for r in rows],
                      key=lambda r: r.get("created_at", ""))

    def emit(self, session: str, event: dict):
        with self.engine.begin() as conn:
            key = conn.execute(insert(self.events).values(session=session,
                payload=json.dumps(event, ensure_ascii=False, allow_nan=False))).inserted_primary_key[0]
        return {**event, "event_id": key}

    def since(self, session: str, after: int = 0):
        with self.engine.connect() as conn:
            rows = conn.execute(select(self.events).where(self.events.c.session == session,
                self.events.c.id > after).order_by(self.events.c.id).limit(300)).mappings().all()
        return [{**json.loads(r["payload"]), "event_id": r["id"]} for r in rows]

    def close(self):
        self.engine.dispose()

    def binding(self, user: str, thread: str, agent: str | None = None):
        key = session_key(user, thread, "binding")
        with self._lock, self.engine.begin() as conn:
            current = conn.execute(select(self.bindings.c.agent).where(self.bindings.c.session == key)).scalar()
            if agent is not None:
                if current is None:
                    conn.execute(insert(self.bindings).values(session=key, agent=agent))
                else:
                    conn.execute(update(self.bindings).where(self.bindings.c.session == key).values(agent=agent))
            return agent if agent is not None else current


def open_checkpointer(stack: ExitStack, root: Path, postgres_dsn: str | None = None):
    if postgres_dsn:
        import psycopg
        from langgraph.checkpoint.postgres import PostgresSaver
        from psycopg.rows import dict_row
        conn = stack.enter_context(psycopg.connect(postgres_dsn, autocommit=True, prepare_threshold=0, row_factory=dict_row))
        conn.execute("CREATE SCHEMA IF NOT EXISTS forecast_memory")
        conn.execute("SET search_path TO forecast_memory")
        saver = PostgresSaver(conn)
    else:
        from langgraph.checkpoint.sqlite import SqliteSaver
        conn = sqlite3.connect(root / "checkpoints.sqlite", check_same_thread=False)
        stack.callback(conn.close)
        saver = SqliteSaver(conn)
    saver.setup()
    return saver
