"""Owned, durable file references. File execution remains in the MCP service."""
from copy import deepcopy
import base64
from datetime import datetime, timezone
from hashlib import sha256
import hmac
import json
import math
import time

from pydantic import BaseModel, ConfigDict
from sqlalchemy import Column, Float, JSON, MetaData, String, Table, Text, and_, cast, func, or_, select

from .contracts import QAError
from .context import project
from .references import at_path


class ArtifactSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    path: str = "/resource"
    consume: str | None = None
    execution_context: bool = False
    replay_safe: bool = False


def execution_metadata(user, request_id, arguments, seconds, *, secret=None):
    """Sign out-of-band execution identity; never put credentials in the model schema."""
    if secret is None:
        from infra.config_loader import get_settings
        secret = get_settings().minio.secret_key
    if seconds <= 0:
        raise QAError("step_limit", "本轮已到处理时限，已取得的结果仍保留")
    if not secret:
        raise QAError("mcp_unavailable", "当前结果存储尚未就绪", 503)
    body = {"user": user, "request_id": request_id,
        "arguments": sha256(_json(_canonical_numbers(arguments)).encode()).hexdigest(),
        "deadline": time.time() + max(1, min(seconds, 480))}
    signature = hmac.new(str(secret).encode(), ("qa-execution-v1\n"+_json(body)).encode(), "sha256").hexdigest()
    return {"piflow_execution": {**body, "signature": signature}}


def _json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _canonical_numbers(value):
    """Execution protocol: equal JSON numbers have one digest on both endpoints.

    Keep booleans, strings and non-integral numbers distinct. This is only for
    argument identity, never the serialization of stored scientific records.
    """
    if isinstance(value, dict):
        return {key: _canonical_numbers(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_canonical_numbers(item) for item in value]
    return int(value) if isinstance(value, float) and value.is_integer() else value


class Artifacts:
    def __init__(self, store):
        self.store = store
        meta = MetaData()
        self.table = Table("dataset_qa_file_artifacts", meta,
            Column("id", String(80), primary_key=True), Column("user_id", String(160), nullable=False, index=True),
            Column("session_id", String(100), nullable=False), Column("result_id", String(180), nullable=False),
            Column("source_key", String(64), nullable=False, index=True), Column("updated_at", Float, nullable=False),
            Column("payload", Text, nullable=False))
        meta.create_all(store.engine)

    def register(self, user, sid, card, tool, spec):
        try:
            resource = at_path(card.get("data"), spec.path)
        except QAError:
            return None
        if resource is None:
            return None
        if (not isinstance(resource, dict) or not isinstance(resource.get("source_ref"), str)
                or not 0 < len(resource["source_ref"]) <= 4000 or type(resource.get("record_count")) is not int
                or resource["record_count"] < 0 or not isinstance(resource.get("format"), str)
                or not 0 < len(resource["format"]) <= 40
                or not isinstance(resource.get("sha256"), str) or len(resource["sha256"]) != 64
                or any(c not in "0123456789abcdef" for c in resource["sha256"])
                or card.get("data", {}).get("record_count", resource["record_count"]) != resource["record_count"]):
            raise QAError("invalid_result", "本次文件信息尚未完整，已保留现有结果", 502)
        identity = sha256(_json([tool.server, resource["source_ref"]]).encode()).hexdigest()
        aid = "artifact-" + sha256(_json([user, identity, resource["sha256"]]).encode()).hexdigest()[:40]
        payload = {"server": tool.server, "tool": tool.name, "path": spec.path, "resource": deepcopy(resource),
            "provenance": {key: card["data"][key] for key in ("query", "statistics", "parent_source_ref", "coverage", "stop_reason")
                if key in card.get("data", {})}}
        row = {"id": aid, "user_id": user, "session_id": sid, "result_id": card["result_id"],
            "source_key": identity, "updated_at": time.time(), "payload": _json(payload)}
        from sqlalchemy.dialects.postgresql import insert as pg_insert
        from sqlalchemy.dialects.sqlite import insert as sqlite_insert
        statement = sqlite_insert if self.store.engine.dialect.name == "sqlite" else pg_insert
        statement = statement(self.table).values(**row)
        statement = statement.on_conflict_do_update(index_elements=["id"],
            set_={key: getattr(statement.excluded, key) for key in row if key != "id"},
            where=self.table.c.updated_at <= statement.excluded.updated_at)
        with self.store.transaction() as conn:
            conn.execute(statement)
        return aid

    def recent(self, user, limit=10):
        with self.store.transaction() as conn:
            rows = conn.execute(select(self.table).where(self.table.c.user_id == user)
                .order_by(self.table.c.updated_at.desc(), self.table.c.id.desc()).limit(limit)).mappings().all()
        return [self._summary(row) for row in rows]

    @staticmethod
    def _summary(row, *, criteria=False):
        payload = json.loads(row["payload"])
        resource = payload["resource"]
        view, cut = project({**{key: resource[key] for key in ("name", "format", "record_count") if key in resource},
            "fields": resource.get("fields", [])[:8]}, 640)
        result = {**(view or {}), "handle": row["id"], "source": payload["server"],
            "updated_at": datetime.fromtimestamp(row["updated_at"], timezone.utc).isoformat()}
        if criteria and (query := payload.get("provenance", {}).get("query")):
            result["criteria"], clipped = project(query, 400)
            cut |= clipped
        if cut:
            result["truncated"] = True
        return result

    def _field(self, *keys):
        # Query existing manifests without a data migration or a second index.
        if self.store.engine.dialect.name == "sqlite":
            return func.json_extract(self.table.c.payload, "$."+".".join(keys))
        value = cast(self.table.c.payload, JSON)
        for key in keys:
            value = value[key]
        return value.as_string()

    def find(self, user, *, query="", source=None, format=None, updated_after=None, updated_before=None, cursor=None, limit=5):
        query = query.strip()
        after = updated_after.timestamp() if updated_after else None
        before = updated_before.timestamp() if updated_before else None
        identity = sha256(_json([user, query, source, format, after, before]).encode()).hexdigest()
        where = [self.table.c.user_id == user]
        if query:
            where.append(or_(self.table.c.id == query, self._field("resource", "name").contains(query, autoescape=True)))
        if source:
            where.append(self._field("server") == source)
        if format:
            where.append(func.lower(self._field("resource", "format")) == format.lower())
        if after is not None:
            where.append(self.table.c.updated_at >= after)
        if before is not None:
            where.append(self.table.c.updated_at < before)
        if cursor:
            try:
                stamp, aid, scope = json.loads(base64.b64decode(cursor, altchars=b"-_", validate=True))
                if (type(stamp) not in {int, float} or not math.isfinite(stamp) or not isinstance(aid, str)
                        or len(aid) > 80 or scope != identity):
                    raise ValueError()
            except (ValueError, TypeError, UnicodeError, OverflowError) as exc:
                raise QAError("invalid_parameters", "查询条件或翻页信息已变化，请从第一页重新查找") from exc
            where.append(or_(self.table.c.updated_at < stamp,
                and_(self.table.c.updated_at == stamp, self.table.c.id < aid)))
        with self.store.transaction() as conn:
            rows = conn.execute(select(self.table).where(*where)
                .order_by(self.table.c.updated_at.desc(), self.table.c.id.desc()).limit(limit+1)).mappings().all()
        page = rows[:limit]
        result = {"items": [self._summary(row, criteria=True) for row in page],
            "guidance": "Saved file candidates only, not new execution. Select a supplied handle for reuse; clarify ambiguous matches. Times are registration/update times in UTC."}
        if len(rows) > limit:
            last = page[-1]
            result["next_cursor"] = base64.urlsafe_b64encode(_json([last["updated_at"], last["id"], identity]).encode()).decode()
        return result

    def get(self, user, aid):
        with self.store.transaction() as conn:
            row = conn.execute(select(self.table).where(self.table.c.id == aid,
                self.table.c.user_id == user)).mappings().first()
        if row is None:
            raise QAError("reference_not_found", "请从当前可用的结果文件中选择", 404)
        return json.loads(row["payload"])

    def reference(self, user, sid, aid):
        item = self.get(user, aid)
        session = self.store.session(user, sid)
        card = self.store.save_resource(user, sid, session["active_task_id"], item["resource"], None)
        return {"result_id": card["result_id"], "path": "", "kind": "object"}

    def authorize(self, user, server, source_ref):
        identity = sha256(_json([server, source_ref]).encode()).hexdigest()
        with self.store.transaction() as conn:
            rows = conn.execute(select(self.table.c.payload).where(self.table.c.user_id == user,
                self.table.c.source_key == identity)).scalars()
            for raw in rows:
                item = json.loads(raw)
                if item["server"] == server and item["resource"]["source_ref"] == source_ref:
                    return
        raise QAError("invalid_parameters", "请先选择已取得的结果文件；不能自行构造资源引用")
