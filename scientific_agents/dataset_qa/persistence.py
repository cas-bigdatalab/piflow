"""Durable sessions, immutable result snapshots and replayable task events."""
from contextlib import contextmanager
from datetime import datetime, timezone
from hashlib import sha256
import json
import threading
import time
from uuid import uuid4

from sqlalchemy import Column, Float, Integer, MetaData, String, Table, Text, UniqueConstraint, delete, func, insert, or_, select, update

from .results import evidence
from .contracts import QAError
from .references import matching_objects


def now():
    return datetime.now(timezone.utc).isoformat()


def dumps(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False)


class Store:
    def __init__(self, engine):
        self.engine, self.lock = engine, threading.RLock()
        meta = MetaData()
        self.sessions = Table("dataset_qa_sessions", meta,
            Column("id", String(100), primary_key=True), Column("user_id", String(160), nullable=False),
            Column("request_id", String(160), nullable=False), Column("title", String(255), nullable=False),
            Column("fingerprint", String(64), nullable=False),
            Column("version", Integer, nullable=False), Column("context", Text, nullable=False),
            Column("active_task_id", String(100)), Column("status", String(24), nullable=False),
            Column("created_at", String(40), nullable=False), Column("updated_at", String(40), nullable=False),
            UniqueConstraint("user_id", "request_id"))
        self.tasks = Table("dataset_qa_tasks", meta,
            Column("id", String(100), primary_key=True), Column("session_id", String(100), nullable=False, index=True),
            Column("request_id", String(160), nullable=False), Column("fingerprint", String(64), nullable=False),
            Column("status", String(24), nullable=False), Column("stage", String(100)), Column("payload", Text, nullable=False),
            Column("owner", String(100), nullable=False), Column("expires", Float, nullable=False),
            Column("created_at", String(40), nullable=False), Column("updated_at", String(40), nullable=False),
            UniqueConstraint("session_id", "request_id"))
        self.items = Table("dataset_qa_items", meta,
            Column("id", Integer, primary_key=True, autoincrement=True), Column("session_id", String(100), nullable=False, index=True),
            Column("task_id", String(100), nullable=False), Column("result_id", String(180), unique=True),
            Column("kind", String(32), nullable=False), Column("role", String(20), nullable=False),
            Column("payload", Text, nullable=False), Column("created_at", String(40), nullable=False))
        self.events = Table("dataset_qa_events", meta,
            Column("id", Integer, primary_key=True, autoincrement=True), Column("task_id", String(100), nullable=False, index=True),
            Column("payload", Text, nullable=False))
        meta.create_all(engine)

    @contextmanager
    def transaction(self):
        # SQLite tests share one connection; PostgreSQL also locks the session
        # row, serializing submissions and writes across service processes.
        with self.lock, self.engine.begin() as conn:
            yield conn

    def _session(self, conn, user, sid, lock=False):
        query = select(self.sessions).where(self.sessions.c.id == sid, self.sessions.c.user_id == user, self.sessions.c.status == "ACTIVE")
        row = conn.execute(query.with_for_update() if lock else query).mappings().first()
        if row is None:
            raise QAError("session_not_found", "会话不存在或无权访问", 404)
        return dict(row)

    def session(self, user, sid):
        with self.transaction() as conn:
            return self._session(conn, user, sid)

    def save_summary(self, user, sid, previous, summary, after):
        with self.transaction() as conn:
            session = self._session(conn, user, sid, True)
            context = json.loads(session["context"])
            if session["active_task_id"] or context.get("summary_after", 0)!=previous:
                return False
            context.update(summary=summary, summary_after=after)
            # This internal cache does not invalidate the frontend's version.
            conn.execute(update(self.sessions).where(self.sessions.c.id==sid).values(context=dumps(context)))
            return True

    def create(self, user, title, request_id):
        with self.transaction() as conn:
            # A deterministic ID makes concurrent create retries converge.
            sid = "qa-" + sha256(dumps([user, request_id]).encode()).hexdigest()[:32]
            stamp = now()
            data = dict(id=sid, user_id=user, request_id=request_id, title=title or "新对话", version=0,
                context=dumps({}), active_task_id=None, status="ACTIVE", created_at=stamp, updated_at=stamp,
                fingerprint=sha256(title.encode()).hexdigest())
            from sqlalchemy.dialects.postgresql import insert as pg_insert
            from sqlalchemy.dialects.sqlite import insert as sqlite_insert
            statement = sqlite_insert if self.engine.dialect.name == "sqlite" else pg_insert
            conn.execute(statement(self.sessions).values(**data).on_conflict_do_nothing(index_elements=["id"]))
            row = conn.execute(select(self.sessions).where(self.sessions.c.id == sid)).mappings().one()
            if row["status"] != "ACTIVE":
                raise QAError("session_deleted", "该创建请求对应的会话已删除", 409)
            if row["fingerprint"] != data["fingerprint"]:
                raise QAError("request_conflict", "请求编号已用于不同内容", 409)
            return dict(row)

    def list_sessions(self, user, page, size, keyword=""):
        with self.transaction() as conn:
            where = [self.sessions.c.user_id == user, self.sessions.c.status == "ACTIVE"]
            if keyword:
                where.append(self.sessions.c.title.contains(keyword, autoescape=True))
            total = conn.scalar(select(func.count()).select_from(self.sessions).where(*where))
            rows = conn.execute(select(self.sessions).where(*where).order_by(self.sessions.c.updated_at.desc(), self.sessions.c.id)
                .offset((page-1)*size).limit(size)).mappings().all()
            return [dict(r) for r in rows], total

    def submit(self, user, sid, request_id, payload, expected_version, owner, after_event_seq=0):
        fingerprint = sha256(dumps(payload).encode()).hexdigest()
        with self.transaction() as conn:
            session = self._session(conn, user, sid, True)
            previous = conn.execute(select(self.tasks).where(self.tasks.c.session_id == sid, self.tasks.c.request_id == request_id)).mappings().first()
            if previous:
                if previous["fingerprint"] != fingerprint:
                    raise QAError("request_conflict", "请求编号已用于不同内容", 409)
                if after_event_seq and not conn.scalar(select(self.events.c.id).where(self.events.c.id == after_event_seq,
                        self.events.c.task_id == previous["id"])):
                    raise QAError("invalid_cursor", "流恢复游标不属于当前请求")
                return dict(previous), False
            if after_event_seq:
                raise QAError("invalid_cursor", "原请求不存在，不能恢复流")
            if expected_version is not None and expected_version != session["version"]:
                raise QAError("version_conflict", "会话已更新，请刷新后重试", 409)
            if session["active_task_id"]:
                raise QAError("session_busy", "当前会话有任务正在处理，请等待或停止后再发送", 409)
            tid, stamp = "qa-task-" + uuid4().hex, now()
            task = dict(id=tid, session_id=sid, request_id=request_id, fingerprint=fingerprint,
                status="RUNNING", stage="understand", payload=dumps(payload), owner=owner, expires=time.time()+45,
                created_at=stamp, updated_at=stamp)
            conn.execute(insert(self.tasks).values(**task))
            claimed = conn.execute(update(self.sessions).where(self.sessions.c.id == sid,
                self.sessions.c.version == session["version"], self.sessions.c.active_task_id.is_(None)).values(active_task_id=tid,
                version=session["version"]+1, title=payload["message"][:80] if session["title"] == "新对话" else session["title"], updated_at=stamp))
            if claimed.rowcount != 1:
                raise QAError("session_busy", "会话已更新，请刷新后重试", 409)
            self._item(conn, sid, tid, "USER_MESSAGE", {"message_id": request_id, "text": payload["message"], "mode": "replace"}, role="user")
            return task, True

    def task(self, user, sid, tid):
        with self.transaction() as conn:
            self._session(conn, user, sid)
            row = conn.execute(select(self.tasks).where(self.tasks.c.id == tid, self.tasks.c.session_id == sid)).mappings().first()
            if row is None:
                raise QAError("task_not_found", "当前会话中不存在此任务", 404)
            return dict(row)

    def task_session(self, user, tid):
        with self.transaction() as conn:
            return conn.scalar(select(self.tasks.c.session_id).join(self.sessions, self.sessions.c.id == self.tasks.c.session_id)
                .where(self.tasks.c.id == tid, self.sessions.c.user_id == user, self.sessions.c.status == "ACTIVE"))

    def _item(self, conn, sid, tid, kind, payload, role="assistant", result_id=None):
        conn.execute(insert(self.items).values(session_id=sid, task_id=tid, kind=kind, role=role,
            payload=dumps(payload), result_id=result_id, created_at=now()))

    def _event(self, conn, tid, data):
        conn.execute(insert(self.events).values(task_id=tid, payload=dumps(data)))

    def write(self, user, sid, tid, data=None, *, context=None, payload=None, card=None, stage=None):
        with self.transaction() as conn:
            session = self._session(conn, user, sid, True)
            row = conn.execute(select(self.tasks).where(self.tasks.c.id == tid, self.tasks.c.session_id == sid)).mappings().first()
            if row is None or row["status"] != "RUNNING" or session["active_task_id"] != tid:
                return False
            changes = {"updated_at": now()}
            if payload is not None:
                changes["payload"] = dumps(payload)
            if data and data["type"] == "stage":
                changes["stage"] = data.get("stage")
            if stage is not None:
                changes["stage"] = stage
            conn.execute(update(self.tasks).where(self.tasks.c.id == tid).values(**changes))
            if context is not None:
                conn.execute(update(self.sessions).where(self.sessions.c.id == sid).values(context=dumps(context),
                    version=session["version"]+1, updated_at=now()))
            if card:
                self._item(conn, sid, tid, "TOOL_RESULT", card, result_id=card["result_id"])
            if data:
                self._event(conn, tid, data)
            return True

    def finish(self, user, sid, tid, status, *, message="", error=None, interaction=None, expired_before=None):
        with self.transaction() as conn:
            session = self._session(conn, user, sid, True)
            row = conn.execute(select(self.tasks).where(self.tasks.c.id == tid, self.tasks.c.session_id == sid)).mappings().first()
            if row is None or row["status"] not in {"RUNNING", "WAITING_INPUT"}:
                return False
            if expired_before is not None and row["expires"] >= expired_before:
                return False
            payload = json.loads(row["payload"])
            if error:
                payload["error"] = error
            if not message and status == "CANCELLED" and row["status"] == "RUNNING":
                for raw in conn.scalars(select(self.events.c.payload).where(self.events.c.task_id == tid).order_by(self.events.c.id)):
                    value = json.loads(raw)
                    if value["type"] == "message":
                        message = value["text"] if value.get("mode") == "replace" else message + value["text"]
            if message:
                self._item(conn, sid, tid, "ASSISTANT_MESSAGE", {"message_id": tid, "text": message, "mode": "replace"})
            if "delivery" in payload and not payload.get("published"):
                result_ids = payload["delivery"]
                self._cards(conn, sid, result_ids)
                for result_id in result_ids:
                    # History references immutable artifacts instead of copying media.
                    self._item(conn, sid, tid, "RESULT_CARD", {"result_id": result_id})
                if result_ids:
                    self._event(conn, tid, {"type": "result", "result_ids": result_ids})
                payload["published"] = True
            if interaction:
                self._event(conn, tid, {"type": "interaction", **interaction})
            conn.execute(update(self.tasks).where(self.tasks.c.id == tid).values(status=status, payload=dumps(payload), updated_at=now()))
            context = json.loads(session["context"])
            if payload.get("published") and payload.get("references"):
                # Publish the display snapshot and its references in the same transaction.
                context["references"] = {**context.get("references", {}), **payload["references"]}
                context["references"] = {key: value for key, value in context["references"].items() if value is not None}
            if status != "WAITING_INPUT" and context.get("pending", {}).get("task_id") == tid:
                context.pop("pending", None)
            conn.execute(update(self.sessions).where(self.sessions.c.id == sid).values(
                active_task_id=None if session["active_task_id"] == tid else session["active_task_id"],
                context=dumps(context), version=session["version"]+1, updated_at=now()))
            done = {"type": "done", "status": status, "version": session["version"]+1}
            if payload.get("error"):
                done.update(code=payload["error"].get("error_code", payload["error"].get("code")),
                    message=payload["error"]["message"])
            self._event(conn, tid, done)
            return True

    def history(self, user, sid, after=0, limit=100, before=None, tail=False):
        with self.transaction() as conn:
            self._session(conn, user, sid)
            return self._history(conn, sid, after, limit, before, tail)

    def _history(self, conn, sid, after, limit, before, tail):
        query = select(self.items).where(self.items.c.session_id == sid, self.items.c.kind != "TOOL_RESULT")
        reverse = tail or before is not None
        query = query.where(self.items.c.id < before) if before is not None else query.where(self.items.c.id > after)
        rows = conn.execute(query.order_by(self.items.c.id.desc() if reverse else self.items.c.id).limit(limit+1)).mappings().all()
        more, rows = len(rows)>limit, rows[:limit]
        rows = [dict(r) for r in (reversed(rows) if reverse else rows)]
        refs = {r["id"]: json.loads(r["payload"])["result_id"] for r in rows
            if r["kind"] == "RESULT_CARD" and set(json.loads(r["payload"])) == {"result_id"}}
        cards = dict(zip(refs, self._cards(conn, sid, list(refs.values()))))
        for row in rows:
            if row["id"] in cards:
                row["payload"] = dumps(cards[row["id"]])
        return rows, more

    def snapshot(self, user, sid, after, limit, before, tail):
        with self.transaction() as conn:
            session = self._session(conn, user, sid, True)
            rows, more = self._history(conn, sid, after, limit, before, tail)
            tids = {r["task_id"] for r in rows}
            if session["active_task_id"]:
                tids.add(session["active_task_id"])
            tasks = conn.execute(select(self.tasks).where(self.tasks.c.id.in_(tids), self.tasks.c.session_id == sid)).mappings().all()
            return session, rows, [dict(t) for t in tasks], more

    def memory(self, user, sid, after=0, before=None, limit=24, tail=False, exclude_task_id=None):
        with self.transaction() as conn:
            self._session(conn, user, sid)
            query = select(self.items).where(self.items.c.session_id == sid, self.items.c.id > after,
                self.items.c.kind.in_(["USER_MESSAGE", "ASSISTANT_MESSAGE"]))
            if before is not None:
                query = query.where(self.items.c.id < before)
            if exclude_task_id:
                query = query.where(self.items.c.task_id != exclude_task_id)
            rows = conn.execute(query.order_by(self.items.c.id.desc() if tail else self.items.c.id).limit(limit)).mappings().all()
            return [{"id": r["id"], "role": r["role"], "text": json.loads(r["payload"])["text"]}
                    for r in (reversed(rows) if tail else rows)]

    def result_refs(self, user, sid, offset, limit):
        with self.transaction() as conn:
            self._session(conn, user, sid)
            rows = list(conn.scalars(select(self.items.c.payload).where(self.items.c.session_id == sid,
                self.items.c.result_id.is_not(None)).order_by(self.items.c.id).offset(offset).limit(limit+1)))
            return [evidence(json.loads(r), 1000) for r in rows[:limit]], len(rows)>limit

    def results(self, user, sid, tid=None, result_id=None):
        with self.transaction() as conn:
            self._session(conn, user, sid)
            query = select(self.items.c.payload).where(self.items.c.session_id == sid, self.items.c.result_id.is_not(None))
            if tid:
                query = query.where(self.items.c.task_id == tid)
            if result_id:
                query = query.where(self.items.c.result_id == result_id)
            query = query.order_by(self.items.c.id.desc())
            if not tid and not result_id:
                query = query.limit(8)
            return [json.loads(r) for r in conn.scalars(query)][::-1]

    def _cards(self, conn, sid, result_ids):
        rows = conn.scalars(select(self.items.c.payload).where(self.items.c.session_id == sid,
            self.items.c.result_id.in_(result_ids)))
        cards = {card["result_id"]: card for card in map(json.loads, rows)}
        if any(result_id not in cards for result_id in result_ids):
            raise QAError("result_not_found", "交付结果不存在或不属于当前会话", 404)
        return [cards[result_id] for result_id in result_ids]

    def selected_results(self, user, sid, result_ids):
        with self.transaction() as conn:
            self._session(conn, user, sid)
            return self._cards(conn, sid, result_ids)

    def latest_display(self, user, sid):
        with self.transaction() as conn:
            self._session(conn, user, sid)
            raw = conn.scalar(select(self.items.c.payload).where(self.items.c.session_id==sid,
                self.items.c.kind=="RESULT_CARD").order_by(self.items.c.id.desc()).limit(1))
            if raw is None:
                return None
            value = json.loads(raw)
            return self._cards(conn, sid, [value["result_id"]])[0] if set(value)=={"result_id"} else value

    def object_reference(self, user, sid, identifier, sources=(), result_id=None):
        """Try explicit/relevant sources first, then lazily search this session's saved results."""
        identifier = str(identifier)
        with self.transaction() as conn:
            self._session(conn, user, sid)
            scopes = [{"result_id": result_id}] if result_id else list(sources)
            seen, cards = set(), {}
            for ref in scopes:
                if ref["result_id"] not in cards:
                    cards[ref["result_id"]] = self._cards(conn, sid, [ref["result_id"]])[0]
                card = cards[ref["result_id"]]
                seen.add(ref["result_id"])
                matches = matching_objects(card, identifier, ref)
                if matches:
                    return matches
            if result_id:
                return []
            # A SQL prefilter avoids decoding every historical artifact. Exact matching
            # and source validation still happen in Python, under the session boundary.
            match = self.items.c.payload.contains(dumps(identifier), autoescape=True)
            if identifier.lstrip("-").isdigit():
                match = or_(match, self.items.c.payload.contains(": "+identifier, autoescape=True))
            query = select(self.items.c.payload).where(self.items.c.session_id==sid,
                self.items.c.result_id.is_not(None), match)
            for raw in conn.scalars(query.order_by(self.items.c.id.desc())):
                card = json.loads(raw)
                if card["result_id"] not in seen:
                    matches = matching_objects(card, identifier)
                    if matches:
                        return matches
            return []

    def display_results(self, user, sid, tid):
        with self.transaction() as conn:
            self._session(conn, user, sid)
            raw = conn.scalar(select(self.tasks.c.payload).where(self.tasks.c.id == tid, self.tasks.c.session_id == sid))
            if raw is None:
                raise QAError("task_not_found", "当前会话中不存在此任务", 404)
            payload = json.loads(raw)
            if "delivery" in payload:
                return self._cards(conn, sid, payload["delivery"]) if payload.get("published") else []
            # Results in older tasks were already public; preserve their history.
            return [json.loads(r) for r in conn.scalars(select(self.items.c.payload).where(
                self.items.c.session_id == sid, self.items.c.task_id == tid,
                self.items.c.kind == "RESULT_CARD").order_by(self.items.c.id))]

    def replay(self, user, sid, tid, after):
        self.task(user, sid, tid)
        with self.transaction() as conn:
            rows = conn.execute(select(self.events).where(self.events.c.task_id == tid, self.events.c.id > after)
                .order_by(self.events.c.id).limit(100)).mappings().all()
            values = []
            for row in rows:
                value = json.loads(row["payload"])
                if value["type"] == "result":
                    if "result_ids" in value:
                        value = {"type": "result", "items": self._cards(conn, sid, value["result_ids"])}
                    else:
                        value = {"type": "result", **self._cards(conn, sid, [value["result_id"]])[0]}
                values.append({**value, "task_id": tid, "event_seq": row["id"]})
            return values

    def heartbeat(self, owner, task_ids=None):
        with self.transaction() as conn:
            query = update(self.tasks).where(self.tasks.c.owner == owner, self.tasks.c.status == "RUNNING")
            if task_ids is not None:
                query = query.where(self.tasks.c.id.in_(task_ids))
            conn.execute(query.values(expires=time.time()+45))
            expired = conn.execute(select(self.tasks.c.id, self.tasks.c.session_id, self.sessions.c.user_id)
                .join(self.sessions, self.sessions.c.id == self.tasks.c.session_id)
                .where(self.tasks.c.status == "RUNNING", self.tasks.c.expires < time.time(), self.sessions.c.status == "ACTIVE")).all()
        for tid, sid, user in expired:
            self.finish(user, sid, tid, "FAILED", error={"code": 503, "error_code": "execution_unknown",
                "message": "任务中断，无法确认上游执行结果；未自动重试"}, expired_before=time.time())
        with self.transaction() as conn:
            return set(conn.scalars(select(self.tasks.c.id).where(self.tasks.c.owner == owner, self.tasks.c.status == "RUNNING")))

    def delete(self, user, sid):
        with self.transaction() as conn:
            session = self._session(conn, user, sid, True)
            tids = select(self.tasks.c.id).where(self.tasks.c.session_id == sid)
            conn.execute(delete(self.events).where(self.events.c.task_id.in_(tids)))
            conn.execute(delete(self.items).where(self.items.c.session_id == sid))
            conn.execute(delete(self.tasks).where(self.tasks.c.session_id == sid))
            conn.execute(update(self.sessions).where(self.sessions.c.id == sid).values(status="DELETED", title="", context="{}", active_task_id=None, updated_at=now()))
            return session["active_task_id"]
