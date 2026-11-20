"""Owned, durable file references. File execution remains in the MCP service."""
from copy import deepcopy
import base64
from datetime import datetime, timezone
from hashlib import sha256
import hmac
import json
import logging
import math
import time
from typing import Literal

from pydantic import BaseModel, ConfigDict
from sqlalchemy import Column, Float, JSON, MetaData, String, Table, Text, and_, cast, func, or_, select

from .contracts import QAError
from .context import project, same_identity
from .references import at_path
from .artifact_storage import canonical_numbers


class ArtifactSpec(BaseModel):
    """Manifest protocol for owned files and structured record resources.

    ``consume`` names a source_ref parameter and accepts the declared kind.
    Structured record exports preserve record_count and parent_source_ref;
    opaque files carry record_count only when measured by their producer.
    """
    model_config = ConfigDict(extra="forbid")
    path: str = "/resource"
    kind: Literal["record_resource", "file"] = "record_resource"
    consume: str | None = None
    execution_context: bool = False
    replay_safe: bool = False


def execution_metadata(user, request_id, arguments, seconds, *, secret=None):
    """Sign out-of-band execution identity; never put credentials in the model schema."""
    if secret is None:
        from .artifact_storage import ArtifactStorageError, signing_key
        try:
            secret = signing_key()
        except ArtifactStorageError as exc:
            logging.getLogger("flow.dataset_qa").warning("Artifact preparation unavailable: phase=%s reason=%s", exc.phase, str(exc))
            raise QAError("artifact_unavailable", "当前结果存储尚未就绪", 503,
                detail={"phase": "execution_context", "dispatched": False}) from exc
    if seconds <= 0:
        raise QAError("step_limit", "本轮已到处理时限，已取得的结果仍保留")
    if not secret:
        raise QAError("artifact_unavailable", "当前结果存储尚未就绪", 503)
    body = {"user": user, "request_id": request_id,
        "arguments": sha256(_json(canonical_numbers(arguments)).encode()).hexdigest(),
        "deadline": time.time() + max(1, min(seconds, 480))}
    signature = hmac.new(str(secret).encode(), ("qa-execution-v1\n"+_json(body)).encode(), "sha256").hexdigest()
    return {"piflow_execution": {**body, "signature": signature}}


def _json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def validate_source_requirements(source, requirements, *, required):
    """Check explicit current constraints against the owned source, never user prose."""
    detail = {"origin": "source_requirements", "dispatched": False,
        "guidance": "For reuse declare this turn's additional source_requirements: criteria parameters and fields, or null to preserve the selected data. "
            "Keep every explicitly requested change; never remove a declared constraint to pass validation. "
            "Export preserves records. Incompatible or unknown source metadata needs the source producer or a supported transformation before export."}
    if requirements is None:
        if not required:
            return
        raise QAError("invalid_parameters", "复用已有文件前须明确本轮数据条件和字段范围", detail=detail)
    expected = requirements.model_dump() if isinstance(requirements, BaseModel) else requirements
    actual = {"criteria": source.get("provenance", {}).get("query"),
        "fields": source["resource"].get("fields")}
    mismatches = []
    if expected["criteria"] and (not isinstance(actual["criteria"], dict) or any(
            key not in actual["criteria"] or not same_identity(value, actual["criteria"][key])
            for key, value in expected["criteria"].items())):
        mismatches.append("criteria")
    if expected["fields"] is not None and not same_identity(expected["fields"], actual["fields"]):
        mismatches.append("fields")
    if mismatches:
        raise QAError("invalid_parameters", "已有文件不符合本轮数据要求，导出不能修改数据选择", detail={
            **detail, "fields": mismatches, "source_requirements": deepcopy(expected)})


class Artifacts:
    def __init__(self, store):
        self.store = store
        meta = MetaData()
        self.table = Table(store.agent_profile.table("file_artifacts"), meta,
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
        count = resource.get("record_count") if isinstance(resource, dict) else None
        if (not isinstance(resource, dict) or not isinstance(resource.get("source_ref"), str)
                or not 0 < len(resource["source_ref"]) <= 4000
                or resource.get("kind", "record_resource") != spec.kind
                or ((spec.kind == "record_resource" or "record_count" in resource) and (type(count) is not int or count < 0))
                or not isinstance(resource.get("format"), str)
                or not 0 < len(resource["format"]) <= 40
                or not isinstance(resource.get("sha256"), str) or len(resource["sha256"]) != 64
                or any(c not in "0123456789abcdef" for c in resource["sha256"])
                or card.get("data", {}).get("record_count", count) != count
                or (spec.kind == "file" and (type(resource.get("size_bytes")) is not int or resource["size_bytes"] < 0
                    or not isinstance(resource.get("name"), str) or not resource["name"]))):
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

    def published(self, user, sid, cards, limit=1800):
        """Resolve actual session deliveries, including merged cards, to owned files.

        A manifest can be registered again in another session, so its latest
        session/result columns cannot establish which files a user just saw.
        Immutable delivery cards and their saved lineage are the authority.
        """
        if not cards:
            return {}
        candidates = []
        with self.store.transaction() as conn:
            self.store._session(conn, user, sid)
            missing = [card["result_id"] for card in cards if not card.get("file_artifact")]
            lineage = {}
            if missing:
                items, tasks = self.store.items, self.store.tasks
                rows = conn.execute(select(items.c.result_id, tasks.c.payload)
                    .join(tasks, tasks.c.id == items.c.task_id)
                    .where(items.c.session_id == sid, items.c.result_id.in_(missing))).all()
                for result_id, raw in rows:
                    links = json.loads(raw).get("delivery_lineage", {}).get(result_id, {})
                    if links:
                        lineage[result_id] = list(dict.fromkeys(links[index]["result_id"]
                            for index in sorted(links, key=int)))
            source_ids = {rid for ids in lineage.values() for rid in ids}
            sources = {}
            if source_ids:
                rows = conn.scalars(select(self.store.items.c.payload).where(
                    self.store.items.c.session_id == sid, self.store.items.c.result_id.in_(source_ids)))
                sources = {card["result_id"]: card for card in map(json.loads, rows)}
            seen = set()
            for display in cards:
                originals = [display] if display.get("file_artifact") else [
                    sources[rid] for rid in lineage.get(display["result_id"], []) if rid in sources]
                for card in originals:
                    handle = card.get("file_artifact")
                    if handle and handle not in seen:
                        seen.add(handle)
                        candidates.append((display["result_id"], card["result_id"], handle))
            if not candidates:
                return {}
            rows = conn.execute(select(self.table).where(self.table.c.user_id == user,
                self.table.c.id.in_(seen))).mappings().all()
            manifests = {row["id"]: json.loads(row["payload"]) for row in rows}
            parent_keys = {handle: sha256(_json([manifest["server"], parent]).encode()).hexdigest()
                for handle, manifest in manifests.items()
                if isinstance(parent := manifest.get("provenance", {}).get("parent_source_ref"), str) and parent}
            parents = {}
            if parent_keys:
                parent_rows = conn.execute(select(self.table.c.source_key, self.table.c.payload)
                    .where(self.table.c.user_id == user, self.table.c.source_key.in_(set(parent_keys.values())))
                    .order_by(self.table.c.updated_at.desc())).all()
                for key, raw in parent_rows:
                    parents.setdefault(key, json.loads(raw))
        result = {"items": [], "total": len(candidates), "guidance": (
            "Compare current requirements with saved criteria, count and fields before reuse. "
            "Reuse compatible records for format-only export, which preserves selection, count and field scope. "
            "Changed requirements need a compatible source result or supported transformation before export; "
            "use the source producer when new retrieval is needed. Never claim export applied new criteria. "
            "Set __qa_object or plan/goal.object to a supplied handle and declare operation/output_format. "
            "Read omitted metadata with read_result using this result_id and its *_path; omission is not compatibility. "
            "Use find_artifacts for older files. Current selections prevail; refs, URLs and paths are not interchangeable.")}
        unavailable = sum(handle not in manifests for _, _, handle in candidates)
        if unavailable:
            result["unavailable"] = unavailable
        if len(_json(result)) + 18 > limit:
            result.pop("guidance")
        # Keep identities complete. Names are optional, and record bodies and
        # signed source references never enter this compact context manifest.
        metadata = []
        for display_id, result_id, handle in candidates:
            if handle not in manifests:
                continue
            manifest = manifests[handle]
            resource = manifest["resource"]
            entry = {"handle": handle, "result_id": result_id, "server": manifest["server"],
                "tool": manifest["tool"], "kind": resource.get("kind", "record_resource"),
                "format": resource["format"]}
            if "record_count" in resource:
                entry["record_count"] = resource["record_count"]
            if parent := parents.get(parent_keys.get(handle)):
                entry["source_producer"] = {"server": parent["server"], "tool": parent["tool"]}
            query = manifest.get("provenance", {}).get("query")
            if query is not None:
                entry.update(criteria_omitted=True, criteria_path="/query")
            if "fields" in resource:
                entry.update(fields_omitted=True, fields_path=manifest["path"].rstrip("/")+"/fields")
            if display_id != result_id:
                entry["display_result_id"] = display_id
            proposal = {**result, "items": [*result["items"], entry], "truncated": True}
            if len(_json(proposal)) > limit:
                break
            result["items"].append(entry)
            metadata.append((query, resource.get("fields"), resource.get("name")))
        if len(result["items"]) + unavailable < result["total"]:
            result["truncated"] = True
        for entry, (query, fields, name) in zip(result["items"], metadata):
            for key, value in (("criteria", query), ("fields", fields)):
                if value is None:
                    continue
                complete, cut = project(value, len(_json(value)))
                if cut or _json(complete) != _json(value):
                    continue  # Sanitization/size must not turn a partial condition into a complete one.
                previous = deepcopy(entry)
                entry[key] = complete
                entry.pop(key+"_omitted", None)
                entry.pop(key+"_path", None)
                if len(_json(result)) > limit:
                    entry.clear()
                    entry.update(previous)
            if name:
                entry["name"] = name
                if len(_json(result)) > limit:
                    entry.pop("name")
        return result if len(_json(result)) <= limit else {}

    @staticmethod
    def _summary(row, *, criteria=False):
        payload = json.loads(row["payload"])
        resource = payload["resource"]
        view, cut = project({**{key: resource[key] for key in ("name", "format", "record_count") if key in resource},
            "fields": resource.get("fields", [])[:8]}, 640)
        result = {**(view or {}), "handle": row["id"], "source": payload["server"],
            "updated_at": datetime.fromtimestamp(row["updated_at"], timezone.utc).isoformat()}
        if resource.get("kind") == "file":
            result["kind"] = "file"
        if criteria and (query := payload.get("provenance", {}).get("query")):
            complete, clipped = project(query, 400)
            if not clipped and _json(complete) == _json(query):
                result["criteria"] = complete
            else:
                result["criteria_omitted"] = True
                cut = True
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
                    return item
        raise QAError("invalid_parameters", "请先选择已取得的结果文件；不能自行构造资源引用")
