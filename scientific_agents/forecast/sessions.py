"""Host session lifecycle and transactional, connection-independent message delivery."""
import logging
import re
import shutil
import threading
import uuid
from concurrent.futures import CancelledError, TimeoutError
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import Column, Integer, MetaData, String, Table, Text, delete, insert, select, text, update

from .persistence import session_key
from .feedback import ForecastError, completion_message

log = logging.getLogger(__name__)
ACTIVE = {"queued", "running", "cancelling"}


def session_times(row):
    """Expose instants, not ambiguous DB wall times; SQLite CURRENT_TIMESTAMP is UTC."""
    result = dict(row)
    for key in ("created_at", "updated_at"):
        value = result.get(key)
        if value is not None:
            value = datetime.fromisoformat(value) if isinstance(value, str) else value
            if value.tzinfo is None:
                value = value.replace(tzinfo=timezone.utc)
            result[key] = value.astimezone(timezone.utc).isoformat()
    return result


class HostSessions:
    def __init__(self, agent):
        self.agent, self.store = agent, agent.store
        self._lock = threading.RLock()
        # Host PostgreSQL columns are TIMESTAMP without time zone, populated by
        # CURRENT_TIMESTAMP in the DB session zone. Resolve that zone in SQL;
        # do not assume it is UTC or change the host's connection settings.
        self._time_columns = ", ".join(
            f"t.{key} AT TIME ZONE current_setting('TimeZone') AS {key}"
            if self.store.engine.dialect.name == "postgresql" else f"t.{key}"
            for key in ("created_at", "updated_at"))
        meta = MetaData()
        self.sessions = Table("forecast_sessions", meta,
            Column("session", String(64), primary_key=True), Column("user_id", String(160)),
            Column("thread_id", String(160)), Column("status", String(20), default="active"))
        self.creations = Table("forecast_session_creations", meta,
            Column("user_id", String(160), primary_key=True),
            Column("request_id", String(160), primary_key=True),
            Column("thread_id", String(160), nullable=False), Column("title", Text, nullable=False))
        # Insert/update the original message and its delivery receipt in ONE DB transaction.
        self.deliveries = Table("forecast_message_deliveries", meta,
            Column("key", String(100), primary_key=True), Column("session", String(64), index=True),
            Column("message_id", Integer), Column("content", Text))
        meta.create_all(self.store.engine)

    def lookup(self, user, thread):
        with self.store.engine.connect() as conn:
            row = conn.execute(select(self.sessions).where(
                self.sessions.c.session == session_key(user, thread))).mappings().first()
        return dict(row) if row else None

    def _metadata(self, conn, user, thread):
        row = conn.execute(text(f"SELECT t.thread_id AS session_id, t.user_id, t.title, {self._time_columns}, "
            "t.deleted, f.status FROM chat_threads t LEFT JOIN forecast_sessions f "
            "ON f.thread_id=t.thread_id AND f.user_id=t.user_id WHERE t.thread_id=:thread"),
            {"thread": thread}).mappings().first()
        if row is None:
            raise HTTPException(404, "会话不存在，请先创建预测会话")
        if str(row["user_id"]) != user:
            raise HTTPException(403, "无权访问会话")
        if row["status"] is None:
            raise HTTPException(404, "预测会话不存在")
        if row["status"] == "deleting":
            raise ForecastError("session_deleting", http_status=409)
        if row["deleted"] or row["status"] != "active":
            raise HTTPException(410, "会话已删除，请新建会话")
        return session_times({key: row[key] for key in ("session_id", "title", "created_at", "updated_at", "status")})

    def require(self, user, thread):
        """Read and authorize only: never create or revive a host conversation."""
        with self.store.engine.connect() as conn:
            return self._metadata(conn, user, thread)

    def create(self, user, request_id, title):
        title = " ".join(title.split())
        # One service process owns this store. The lock serializes creates/deletes;
        # the DB primary key also enforces user-scoped creation request uniqueness.
        with self._lock, self.store.engine.begin() as conn:
            previous = conn.execute(select(self.creations).where(
                self.creations.c.user_id == user, self.creations.c.request_id == request_id)).mappings().first()
            if previous:
                if previous["title"] != title:
                    raise HTTPException(409, "同一创建请求编号不能对应不同标题")
                return self._metadata(conn, user, previous["thread_id"])
            thread = "forecast-" + uuid.uuid4().hex
            conn.execute(text("INSERT INTO chat_threads (thread_id,user_id,title,deleted) "
                "VALUES (:thread,:user,:title,FALSE)"), {"thread": thread, "user": user, "title": title})
            conn.execute(insert(self.sessions).values(session=session_key(user, thread),
                user_id=user, thread_id=thread, status="active"))
            conn.execute(insert(self.creations).values(user_id=user, request_id=request_id,
                thread_id=thread, title=title))
            return self._metadata(conn, user, thread)

    def list(self, user, page, size):
        join = ("FROM chat_threads t JOIN forecast_sessions f ON f.thread_id=t.thread_id "
                "AND f.user_id=t.user_id WHERE t.user_id=:user AND t.deleted=FALSE AND f.status='active'")
        with self.store.engine.connect() as conn:
            total = conn.execute(text("SELECT count(*) " + join), {"user": user}).scalar_one()
            rows = conn.execute(text(f"SELECT t.thread_id AS session_id,t.title,{self._time_columns},f.status "
                + join + " ORDER BY t.updated_at DESC,t.id DESC LIMIT :size OFFSET :offset"),
                {"user": user, "size": size, "offset": (page - 1) * size}).mappings().all()
        return {"sessions": [session_times(row) for row in rows], "total": total, "pageNum": page, "pageSize": size}

    def _deliver(self, owner, key, role, content, existing_id=None):
        with self.store.engine.begin() as conn:
            receipt = conn.execute(select(self.deliveries).where(self.deliveries.c.key == key)).mappings().first()
            if receipt and receipt["content"] == content:
                return
            values = dict(user=owner["user_id"], thread=owner["thread_id"], role=role, content=content)
            if receipt:
                conn.execute(text("UPDATE messages SET content=:content WHERE id=:id AND user_id=:user AND thread_id=:thread"),
                             {**values, "id": receipt["message_id"]})
                conn.execute(update(self.deliveries).where(self.deliveries.c.key == key).values(content=content))
            else:
                if existing_id is not None:
                    message_id = conn.execute(text("SELECT id FROM messages WHERE id=:id AND user_id=:user "
                        "AND thread_id=:thread AND role=:role AND content=:content"), {**values, "id": existing_id}).scalar_one()
                else:
                    message_id = conn.execute(text("INSERT INTO messages (user_id, thread_id, role, content) "
                        "VALUES (:user, :thread, :role, :content) RETURNING id"), values).scalar_one()
                conn.execute(insert(self.deliveries).values(key=key, session=owner["session"],
                    message_id=message_id, content=content))
            if role == "user":
                conn.execute(text("UPDATE chat_threads SET title=:title WHERE thread_id=:thread "
                                  "AND user_id=:user AND title=''"),
                             {**values, "title": " ".join(content.split())[:255]})
            conn.execute(text("UPDATE chat_threads SET updated_at=CURRENT_TIMESTAMP WHERE thread_id=:thread AND user_id=:user"), values)

    def sync(self, session):
        with self._lock:
            with self.store.engine.connect() as conn:
                owner = conn.execute(select(self.sessions).where(self.sessions.c.session == session)).mappings().first()
            if not owner or owner["status"] != "active":
                return
            turns = self.store.list_turns(session)
            for turn in turns:
                self._deliver(owner, turn["id"] + ":user", "user", turn["input"], turn.get("message_id"))
                self._deliver(owner, turn["id"] + ":assistant", "assistant", turn["response"]["content"])
            recorded_runs = {turn["response"].get("run_id") for turn in turns}
            for task in reversed(self.store.list_tasks(session)):
                if task["status"] in ACTIVE or task["run_id"] not in recorded_runs:
                    continue
                if task["status"] == "completed":
                    try:
                        content = completion_message(self.agent.result(task["run_id"], session))
                    except ForecastError as exc:
                        if exc.code != "result_unavailable":
                            raise
                        if task.get("result_available") is not False:
                            self.store.put_task(task["run_id"], session, "completed",
                                result_available=False, result_problem=exc.problem())
                            log.warning("Forecast result unavailable; history retained: %s", task["run_id"])
                        # Preserve previously delivered scientific text. A missing
                        # artifact must not erase it or block other task deliveries.
                        with self.store.engine.connect() as conn:
                            delivered = conn.execute(select(self.deliveries.c.key).where(
                                self.deliveries.c.key == task["run_id"] + ":result")).first()
                        if delivered:
                            continue
                        content = "这次预测的完成记录仍在，但结果文件暂时不可读取。请检查结果存储或恢复原任务目录；文件恢复后会自动更新这里的结果。"
                    else:
                        if task.get("result_available") is not True:
                            self.store.put_task(task["run_id"], session, "completed",
                                result_available=True, result_problem=None)
                else:
                    content = "任务状态：" + task["status"] + "。" + task.get("error", "")
                self._deliver(owner, task["run_id"] + ":result", "assistant", content)

    def sync_safely(self, session):
        try:
            self.sync(session)
        except Exception:
            # Durable turns/tasks are the outbox; the next sweep retries delivery.
            log.exception("Forecast message delivery deferred for session %s", session)

    def reconcile(self):
        with self.store.engine.connect() as conn:
            rows = conn.execute(select(self.sessions)).mappings().all()
        for row in rows:
            try:
                if row["status"] == "deleting":
                    self.delete(row["user_id"], row["thread_id"])
                elif row["status"] == "active":
                    self.sync(row["session"])
            except Exception:
                log.exception("Forecast session reconciliation deferred")

    def history(self, user, thread, after=0, limit=100):
        session = session_key(user, thread)
        self.sync(session)
        created_at = ("m.created_at AT TIME ZONE current_setting('TimeZone')"
                      if self.store.engine.dialect.name == "postgresql" else "m.created_at")
        with self.store.engine.connect() as conn:
            rows = conn.execute(text(f"SELECT m.id, m.role, m.content, {created_at} AS created_at, d.key AS delivery_key FROM messages m "
                "JOIN forecast_message_deliveries d ON d.message_id=m.id "
                "WHERE d.session=:session AND m.id>:after ORDER BY m.id LIMIT :limit"),
                dict(session=session, after=after, limit=limit)).mappings().all()
        messages = []
        for row in rows:
            message = session_times(row)
            message["create_time"] = message.pop("created_at")
            key, kind = message.pop("delivery_key").rsplit(":", 1)
            message["reply_id"] = ("reply-" if kind == "assistant" else "result-" if kind == "result" else "user-") + key
            if kind == "result":
                message["run_id"] = key
            messages.append(message)
        return messages

    def validate_message(self, user, thread, message_id, content):
        if message_id is None:
            return
        with self.store.engine.connect() as conn:
            found = conn.execute(text("SELECT id FROM messages WHERE id=:id AND user_id=:user "
                "AND thread_id=:thread AND role='user' AND content=:content"),
                dict(id=message_id, user=user, thread=thread, content=content)).scalar()
        if found is None:
            raise HTTPException(422, "消息编号必须对应当前会话中已保存的同一条用户消息")

    def delete(self, user, thread):
        session = session_key(user, thread)
        # Same lock order as turn(): agent -> session. Never wait for a worker while holding these locks.
        with self.agent._lock, self._lock:
            row = self.lookup(user, thread)
            if not row or row["status"] == "deleted":
                return True
            with self.store.engine.begin() as conn:
                conn.execute(update(self.sessions).where(self.sessions.c.session == session).values(status="deleting"))
            tasks = self.store.list_tasks(session)
            for task in tasks:
                if task["status"] in ACTIVE:
                    self.agent.runner.stop(task["run_id"], session)
        for task in tasks:
            job = self.agent._jobs.get(task["run_id"])
            if job:
                try:
                    job.result(timeout=1)  # Leave a deleting tombstone until the actual worker exits.
                except CancelledError:
                    pass
                except TimeoutError:
                    return False
        with self.agent._lock, self._lock:
            root = (self.agent.workflow.settings.root / "runs").resolve()
            for task in tasks:
                run_id = task["run_id"]
                target = (root / run_id).resolve()
                if not re.fullmatch(r"fc-[0-9a-f]{24}", run_id) or target.parent != root:
                    raise ValueError("无效的任务清理路径")
                if target.exists():
                    shutil.rmtree(target)
                self.agent._jobs.pop(run_id, None)
            self.agent.checkpointer.delete_thread(session)
            with self.store.engine.begin() as conn:
                conn.execute(text("DELETE FROM messages WHERE id IN "
                    "(SELECT message_id FROM forecast_message_deliveries WHERE session=:session)"), {"session": session})
                for table in [self.deliveries, self.store.tasks, self.store.turns, self.store.events]:
                    conn.execute(delete(table).where(table.c.session == session))
                conn.execute(delete(self.store.bindings).where(self.store.bindings.c.session == session_key(user, thread, "binding")))
                conn.execute(text("UPDATE chat_threads SET deleted=TRUE WHERE user_id=:user AND thread_id=:thread"),
                             {"user": user, "thread": thread})
                # Retain only a tombstone to reject late retries and prevent resurrection.
                conn.execute(update(self.sessions).where(self.sessions.c.session == session).values(status="deleted"))
        return True
