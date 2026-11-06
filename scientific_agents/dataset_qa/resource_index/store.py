"""User-scoped tree snapshots and leased work; never writes conversation state."""
from contextlib import contextmanager
import json
import time
from uuid import uuid4

from sqlalchemy import Column, Float, Index, Integer, MetaData, String, Table, Text, and_, delete, func, insert, or_, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from ..contracts import QAError
from .model import DirectorySpec, IndexPolicy, digest

ROOT = "root"


def dump(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False)


class IndexStore:
    def __init__(self, engine, lock, policy=None):
        self.engine, self.lock, self.policy = engine, lock, policy or IndexPolicy()
        meta = MetaData()
        self.scopes = Table("dataset_qa_resource_scopes", meta,
            Column("id", String(64), primary_key=True), Column("user_id", String(160), nullable=False, index=True),
            Column("server", String(255), nullable=False), Column("source", String(64), nullable=False),
            Column("tool", String(255), nullable=False), Column("arguments", Text, nullable=False),
            Column("descriptor", Text, nullable=False), Column("dataset", Text, nullable=False),
            Column("generation", Integer, nullable=False), Column("published", Integer, nullable=False),
            Column("state", String(24), nullable=False), Column("owner", String(64)),
            Column("lease", Float, nullable=False), Column("priority", Integer, nullable=False),
            Column("updated", Float, nullable=False))
        self.nodes = Table("dataset_qa_resource_nodes", meta,
            Column("scope", String(64), primary_key=True), Column("generation", Integer, primary_key=True),
            Column("key", String(64), primary_key=True), Column("parent", String(64)),
            Column("identity", Text, nullable=False), Column("name", Text, nullable=False),
            Column("path", Text, nullable=False), Column("kind", String(16), nullable=False),
            Column("record", Text, nullable=False), Column("pointer", Text, nullable=False),
            Column("depth", Integer, nullable=False), Column("state", String(24), nullable=False),
            Column("attempts", Integer, nullable=False), Column("due", Float, nullable=False),
            Column("observed", Float, nullable=False))
        Index("ix_qa_resource_name", self.nodes.c.scope, self.nodes.c.generation, self.nodes.c.name)
        Index("ix_qa_resource_parent", self.nodes.c.scope, self.nodes.c.generation, self.nodes.c.parent)
        # Atomic slots bound background MCP concurrency across service processes.
        self.slots = Table("dataset_qa_resource_slots", meta,
            Column("id", Integer, primary_key=True), Column("owner", String(64)), Column("lease", Float, nullable=False))
        with self.lock:
            meta.create_all(engine)
            with engine.begin() as conn:
                for number in range(self.policy.workers):
                    self._insert(conn, self.slots, {"id": number, "lease": 0})

    @contextmanager
    def transaction(self):
        # The host lock also protects tests using SQLite's shared connection.
        with self.lock, self.engine.begin() as conn:
            yield conn

    def _insert(self, conn, table, value):
        factory = sqlite_insert if conn.dialect.name=="sqlite" else pg_insert
        conn.execute(factory(table).values(**value).on_conflict_do_nothing())

    def _node_where(self, scope, key=None):
        values = [self.nodes.c.scope==scope["id"], self.nodes.c.generation==scope["generation"]]
        if key is not None:
            values.append(self.nodes.c.key==key)
        return and_(*values)

    def _root(self, conn, scope):
        self._insert(conn, self.nodes, {"scope": scope["id"], "generation": scope["generation"], "key": ROOT,
            "parent": None, "identity": "null", "name": "", "path": "", "kind": "directory", "record": "{}",
            "pointer": "", "depth": 0, "state": "pending", "attempts": 0, "due": 0, "observed": 0})

    def observe(self, user, tool, source, arguments, data, dataset):
        from ..capabilities import profile
        from ..context import pointer_tokens
        spec = profile(tool).directory
        rows = spec.rows(data)
        base = spec.base(arguments)
        supplied_dataset = dataset is not None
        if dataset is None:
            # Direct user-supplied identifiers are grounded by the successful
            # call. Map them back through the declared source-field binding.
            dataset = {}
            for key, paths in profile(tool).bind.items():
                if key not in base:
                    continue
                tokens = pointer_tokens(paths[0])
                target = dataset
                for token in tokens[:-1]:
                    target = target.setdefault(token, {})
                if tokens:
                    target[tokens[-1]] = base[key]
        key = digest([user, tool.server, source, tool.name, base])
        now = time.time()
        with self.transaction() as conn:
            self._insert(conn, self.scopes, {"id": key, "user_id": user, "server": tool.server, "source": source,
                "tool": tool.name, "arguments": dump(base), "descriptor": spec.model_dump_json(),
                "dataset": dump({"record": dataset or base, "bind": profile(tool).bind}),
                "generation": 1, "published": 0, "state": "queued",
                "lease": 0, "priority": 0, "updated": now})
            scope = dict(conn.execute(select(self.scopes).where(self.scopes.c.id==key).with_for_update()).mappings().one())
            if supplied_dataset:
                conn.execute(update(self.scopes).where(self.scopes.c.id==key).values(
                    dataset=dump({"record": dataset, "bind": profile(tool).bind})))
            self._root(conn, scope)
            parent = arguments.get(spec.parent)
            parent_key = ROOT if parent is None else digest(parent)
            # An arbitrary subtree response cannot establish its ancestry.
            # Queue the root first rather than invent a parent relationship.
            if parent is None or conn.scalar(select(self.nodes.c.key).where(self._node_where(scope, parent_key))):
                self._ingest(conn, scope, parent_key, rows, now)
        return key

    def _ingest(self, conn, scope, parent_key, rows, observed):
        parent = conn.execute(select(self.nodes).where(self._node_where(scope, parent_key))).mappings().one()
        if parent["depth"]>=self.policy.max_depth and rows:
            raise QAError("index_limit", "目录层级超过索引预算")
        keys = [row["key"] for row in rows]
        if len(keys)!=len(set(keys)):
            raise QAError("invalid_schema", "同一目录返回了重复的节点身份")
        existing = {row["key"]: dict(row) for row in conn.execute(select(self.nodes).where(self._node_where(scope),
            or_(self.nodes.c.parent==parent_key, self.nodes.c.key.in_(keys)))).mappings()}
        count = conn.scalar(select(func.count()).select_from(self.nodes).where(self._node_where(scope)))
        if count+len(set(keys)-existing.keys())>self.policy.max_nodes:
            raise QAError("index_limit", "目录节点超过索引预算")
        children, additions = set(), []
        for row in rows:
            key, old = row["key"], existing.get(row["key"])
            children.add(key)
            if key==parent_key or (old and old["parent"]!=parent_key):
                # Repeated directory IDs may be aliases/cycles. Do not follow
                # them again or silently assign one file to two locations.
                raise QAError("invalid_schema", "目录节点身份存在循环或归属冲突")
            path = (parent["path"].rstrip("/")+"/" if parent["path"] else "")+row["name"]
            if old and (old["kind"]!=row["kind"] or (old["kind"]=="directory" and old["name"]!=row["name"])):
                self._remove_branch(conn, scope, old)
                old = None
            value = {"scope": scope["id"], "generation": scope["generation"], "key": key, "parent": parent_key,
                "identity": dump(row["identity"]), "name": row["name"], "path": path, "kind": row["kind"],
                "record": dump(row["raw"]), "pointer": row["pointer"], "depth": parent["depth"]+1,
                "state": old["state"] if old else "done" if row["kind"]=="file" else "pending",
                "attempts": old["attempts"] if old else 0, "due": old["due"] if old else 0,
                "observed": old["observed"] if old and row["kind"]=="directory" else observed}
            if old:
                conn.execute(update(self.nodes).where(self._node_where(scope, key)).values(**value))
            else:
                additions.append(value)
        if additions:
            conn.execute(insert(self.nodes), additions)
        # Removal is justified only by a successful, complete listing of this
        # parent. Failed or differently shaped payloads never reach this code.
        for old in existing.values():
            if old["parent"]==parent_key and old["key"] not in children:
                self._remove_branch(conn, scope, old)
        conn.execute(update(self.nodes).where(self._node_where(scope, parent_key)).values(
            state="done", attempts=0, due=0, observed=observed))
        self._state(conn, scope)

    def _remove_branch(self, conn, scope, node):
        conn.execute(delete(self.nodes).where(self._node_where(scope), self.nodes.c.key.in_(self._subtree(scope, node["key"]))))

    def _subtree(self, scope, key):
        tree = select(self.nodes.c.key).where(self._node_where(scope, key)).cte(recursive=True)
        tree = tree.union_all(select(self.nodes.c.key).join(tree, self.nodes.c.parent==tree.c.key)
            .where(self._node_where(scope)))
        return select(tree.c.key)

    def _state(self, conn, scope):
        states = set(conn.scalars(select(self.nodes.c.state).where(self._node_where(scope), self.nodes.c.kind=="directory")))
        state = "queued" if states & {"pending", "running"} else "partial" if "failed" in states else "complete"
        values = {"state": state, "updated": time.time()}
        if state=="complete":
            values.update(published=scope["generation"], priority=0)
            conn.execute(delete(self.nodes).where(self.nodes.c.scope==scope["id"],
                self.nodes.c.generation<scope["generation"]-1))
        conn.execute(update(self.scopes).where(self.scopes.c.id==scope["id"]).values(**values))

    def claim(self, sources, *, foreground=False):
        owner = uuid4().hex
        if not sources:
            return None
        with self.transaction() as conn:
            now = time.time()
            slot = None
            for number in range(self.policy.workers):
                if conn.execute(update(self.slots).where(self.slots.c.id==number, self.slots.c.lease<=now)
                        .values(owner=owner, lease=now+self.policy.lease_seconds)).rowcount:
                    slot = number
                    break
            if slot is None:
                return None
            where = [self.scopes.c.state.in_(["queued", "building"]), self.scopes.c.lease<=now,
                or_(*(and_(self.scopes.c.server==name, self.scopes.c.source==identity) for name, identity in sources.items()))]
            if foreground:
                where.append(self.scopes.c.priority>0)
            scopes = conn.execute(select(self.scopes).where(*where).order_by(
                self.scopes.c.priority.desc(), self.scopes.c.updated).with_for_update(skip_locked=True)).mappings()
            for value in scopes:
                scope = dict(value)
                node = conn.execute(select(self.nodes).where(self._node_where(scope), self.nodes.c.kind=="directory",
                    self.nodes.c.state.in_(["pending", "running"]), self.nodes.c.due<=now)
                    .order_by(self.nodes.c.depth, self.nodes.c.key).limit(1)).mappings().first()
                if node is None:
                    continue
                if not conn.execute(update(self.scopes).where(self.scopes.c.id==scope["id"], self.scopes.c.lease<=now)
                        .values(owner=owner, lease=now+self.policy.lease_seconds, state="building")).rowcount:
                    continue
                conn.execute(update(self.nodes).where(self._node_where(scope, node["key"])).values(state="running"))
                return {"scope": scope, "node": dict(node), "owner": owner, "slot": slot}
            conn.execute(update(self.slots).where(self.slots.c.id==slot, self.slots.c.owner==owner).values(owner=None, lease=0))
        return None

    def finish(self, job, rows=None, error=None, *, retry=False):
        scope, node = job["scope"], job["node"]
        with self.transaction() as conn:
            current = conn.execute(select(self.scopes).where(self.scopes.c.id==scope["id"]).with_for_update()).mappings().first()
            if current and current["owner"]==job["owner"] and current["generation"]==scope["generation"]:
                latest = conn.execute(select(self.nodes).where(self._node_where(scope, node["key"]))).mappings().first()
                # Compare the claimed snapshot, not a wall-clock timestamp
                # taken before waiting for a database lock. Otherwise a newly
                # discovered node can look newer than its own claimant.
                if latest and latest["state"]=="running" and latest["observed"]==node["observed"]:
                    if rows is not None:
                        self._ingest(conn, scope, node["key"], rows, time.time())
                    else:
                        attempts = latest["attempts"]+1
                        pending = retry and attempts<=self.policy.retries
                        conn.execute(update(self.nodes).where(self._node_where(scope, node["key"])).values(
                            state="pending" if pending else "failed", attempts=attempts,
                            due=time.time()+(min(30, 2**attempts) if pending else self.policy.refresh_backoff)))
                        self._state(conn, scope)
                conn.execute(update(self.scopes).where(self.scopes.c.id==scope["id"]).values(owner=None, lease=0))
            conn.execute(update(self.slots).where(self.slots.c.id==job["slot"], self.slots.c.owner==job["owner"])
                .values(owner=None, lease=0))

    def release(self, job):
        # On service shutdown, leave the node pending without consuming retry.
        with self.transaction() as conn:
            scope = job["scope"]
            if conn.execute(update(self.scopes).where(self.scopes.c.id==scope["id"], self.scopes.c.owner==job["owner"],
                    self.scopes.c.generation==scope["generation"]).values(owner=None, lease=0, state="queued")).rowcount:
                conn.execute(update(self.nodes).where(self._node_where(scope, job["node"]["key"]),
                    self.nodes.c.state=="running").values(state="pending"))
            conn.execute(update(self.slots).where(self.slots.c.id==job["slot"], self.slots.c.owner==job["owner"])
                .values(owner=None, lease=0))

    def scope(self, user, key, sources):
        with self.transaction() as conn:
            value = conn.execute(select(self.scopes).where(self.scopes.c.id==key, self.scopes.c.user_id==user)).mappings().first()
            if value is None or sources.get(value["server"])!=value["source"]:
                raise QAError("reference_not_found", "资源索引不属于当前可用范围")
            return dict(value)

    def scopes_for(self, user, sources, record=None, dataset=None):
        from ..capabilities import same_identity
        from ..references import at_path, matching_objects

        with self.transaction() as conn:
            rows = conn.execute(select(self.scopes).where(self.scopes.c.user_id==user)).mappings()
            matches = []
            for row in rows:
                if sources.get(row["server"])!=row["source"]:
                    continue
                stored = json.loads(row["dataset"])
                if dataset is not None and not matching_objects({"result_id": row["id"], "data": stored["record"]}, dataset):
                    continue
                if record is not None:
                    arguments = json.loads(row["arguments"])
                    spec = DirectorySpec.model_validate_json(row["descriptor"])
                    for key in spec.identity:
                        values = []
                        for path in stored["bind"].get(key, []):
                            try:
                                values.append(at_path(record, path))
                            except QAError:
                                pass
                        values = [value for value in values if value is not None and value!=""]
                        if not values or not all(same_identity(value, arguments[key]) for value in values):
                            break
                    else:
                        matches.append(dict(row))
                    continue
                matches.append(dict(row))
            return matches

    def refresh(self, user, key, sources, parent=None, *, full=False):
        self.scope(user, key, sources)
        with self.transaction() as conn:
            scope = dict(conn.execute(select(self.scopes).where(self.scopes.c.id==key).with_for_update()).mappings().one())
            if full and scope["state"] not in {"queued", "building"}:
                scope["generation"] += 1
                conn.execute(update(self.scopes).where(self.scopes.c.id==key).values(
                    generation=scope["generation"], owner=None, lease=0))
                self._root(conn, scope)
                conn.execute(delete(self.nodes).where(self.nodes.c.scope==key,
                    self.nodes.c.generation.not_in([scope["published"], scope["generation"]])))
            elif parent:
                conn.execute(update(self.nodes).where(self._node_where(scope, parent), self.nodes.c.kind=="directory",
                    or_(self.nodes.c.state=="done", and_(self.nodes.c.state=="failed", self.nodes.c.due<=time.time())))
                    .values(state="pending", attempts=0, due=0))
            elif scope["state"]=="partial":
                conn.execute(update(self.nodes).where(self._node_where(scope), self.nodes.c.state=="failed")
                    .values(state="pending", attempts=0, due=0))
            conn.execute(update(self.scopes).where(self.scopes.c.id==key).values(priority=1))
            self._state(conn, scope)

    def prioritize(self, user, key, sources):
        self.scope(user, key, sources)
        with self.transaction() as conn:
            conn.execute(update(self.scopes).where(self.scopes.c.id==key,
                self.scopes.c.state.in_(["queued", "building"])).values(priority=1))

    def lookup(self, user, sources, name, *, scope_id=None, parent=None, kind="file", limit=10):
        now, matches, complete, found_scopes, stale, pending = time.time(), [], True, [], [], False
        with self.transaction() as conn:
            query = select(self.scopes).where(self.scopes.c.user_id==user)
            if scope_id:
                query = query.where(self.scopes.c.id==scope_id)
            for value in conn.execute(query).mappings():
                scope = dict(value)
                if sources.get(scope["server"])!=scope["source"]:
                    continue
                found_scopes.append(scope["id"])
                pending = pending or scope["state"] in {"queued", "building"}
                generation = scope["generation"]
                base = and_(self.nodes.c.scope==scope["id"], self.nodes.c.generation==generation)
                narrowed = None
                if parent:
                    narrowed = conn.execute(select(self.nodes).where(base, self.nodes.c.key==parent)).mappings().first()
                    if narrowed is None:
                        complete = False
                        continue
                    base = and_(base, self.nodes.c.key.in_(self._subtree(scope, parent)))
                ready = (not conn.scalar(select(func.count()).select_from(self.nodes).where(base,
                    self.nodes.c.kind=="directory", self.nodes.c.state!="done")))
                complete = complete and ready
                where = [base, self.nodes.c.kind==kind, or_(self.nodes.c.name==name, self.nodes.c.path==name)]
                rows = list(conn.execute(select(self.nodes).where(*where).order_by(self.nodes.c.path).limit(limit+1)).mappings())
                root_time = conn.scalar(select(self.nodes.c.observed).where(self._node_where(scope, parent or ROOT))) or 0
                if ready and not rows and now-root_time>self.policy.freshness:
                    stale.append(scope["id"])
                    complete = False
                if not rows and scope["published"] and scope["published"]!=generation and not parent:
                    # Old complete snapshots provide hints during rebuilding,
                    # never a claim of current uniqueness.
                    rows = list(conn.execute(select(self.nodes).where(self.nodes.c.scope==scope["id"],
                        self.nodes.c.generation==scope["published"], self.nodes.c.kind==kind,
                        or_(self.nodes.c.name==name, self.nodes.c.path==name)).limit(limit+1)).mappings())
                    ready, complete = False, False
                for row in rows:
                    matches.append({**dict(row), "dataset": json.loads(scope["dataset"])["record"],
                        "arguments": json.loads(scope["arguments"]), "server": scope["server"], "source": scope["source"],
                        "tool": scope["tool"], "fresh": now-row["observed"]<=self.policy.freshness,
                        "complete": ready, "descriptor": json.loads(scope["descriptor"])})
        return {"items": matches[:limit], "more": len(matches)>limit,
                "complete": complete and bool(found_scopes), "scopes": found_scopes, "stale": stale, "pending": pending}
