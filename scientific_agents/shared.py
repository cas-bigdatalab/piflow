"""Shared storage and compatibility with the unchanged host chat routes."""
import asyncio
from hashlib import sha256
import json
import threading

from fastapi import HTTPException
from sqlalchemy import Column, MetaData, String, Table, create_engine, inspect, insert, select, update


def session_key(user: str, thread: str, agent: str = "forecast") -> str:
    return sha256(json.dumps([user, thread, agent]).encode()).hexdigest()


class BindingStore:
    """Keep the existing binding table and keys, independently of forecast startup."""

    def __init__(self, url: str, *, shared=None):
        self._owns_engine = shared is None
        if shared is not None:
            self.engine, self.bindings, self._lock = shared.engine, shared.bindings, shared._lock
            return
        self.engine = create_engine(url, pool_pre_ping=True,
            connect_args={"check_same_thread": False, "timeout": 30} if url.startswith("sqlite") else {})
        self._lock = threading.RLock()
        meta = MetaData()
        self.bindings = Table("forecast_bindings", meta,
            Column("session", String(64), primary_key=True), Column("agent", String(80)))
        try:
            meta.create_all(self.engine)
        except BaseException:
            self.close()
            raise

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

    def close(self):
        if self._owns_engine:
            self.engine.dispose()


class StoredSessions:
    """Ownership checks without importing or starting a disabled agent."""

    def __init__(self, engine, table_name, id_column):
        self.engine = engine
        self.table = None
        if inspect(engine).has_table(table_name):
            self.table = Table(table_name, MetaData(),
                Column(id_column, String), Column("user_id", String))
        self.id_column = id_column

    def lookup(self, user, sid):
        if self.table is None:
            return None
        with self.engine.connect() as conn:
            row = conn.execute(select(self.table).where(
                self.table.c[self.id_column] == sid, self.table.c.user_id == str(user))).mappings().first()
        return dict(row) if row else None


class QASessions:
    """Adapt QA's existing session methods to the host's lookup/delete interface."""

    def __init__(self, service):
        self.service = service

    def lookup(self, user, sid):
        from .dataset_qa.contracts import QAError

        try:
            return self.service.store.session(user, sid)
        except QAError as exc:
            if exc.status != 404:
                raise
            return None

    async def delete(self, user, sid, request):
        from .dataset_qa.contracts import QAError

        try:
            return await self.service.delete_session(user, sid)
        except QAError as exc:
            raise HTTPException(exc.status, str(exc)) from exc


class SharedState:
    def __init__(self, store, enabled_agents):
        self.store = store
        self.enabled_agents = frozenset(enabled_agents)
        self.agent_states = {}
        self.session_services = {}
        self.deleters = {}
        # The host's getattr default evaluates extension.sessions even when the
        # session_services attribute exists. Keep that interface without forecast.
        self.sessions = None

    @staticmethod
    def check_host_user(user, request):
        from security.auth_dependency import get_current_user

        auth = request.headers.get("authorization", "")
        if not auth.startswith("Bearer "):
            raise HTTPException(401, "请使用原项目的登录凭证")
        if str(get_current_user(token=auth[7:])["user_id"]) != str(user):
            raise HTTPException(403, "登录用户与会话用户不一致")

    def owner(self, user, sid, *, disabled_only=False):
        bound = self.store.binding(user, "unified:" + sid)
        if bound:
            return bound
        matches = [key for key, service in self.session_services.items()
            if (not disabled_only or key not in self.enabled_agents) and service.lookup(user, sid)]
        if len(matches) > 1:
            raise HTTPException(409, "会话归属不唯一")
        return matches[0] if matches else None

    async def delete_host_session(self, user, sid, request):
        self.check_host_user(user, request)
        owner = await asyncio.to_thread(self.owner, user, sid)
        if owner not in self.enabled_agents:
            raise HTTPException(409 if owner else 404,
                "该智能体已停用，请启用后再操作" if owner else "会话不存在或无权访问")
        await self.deleters[owner](user, sid, request)
