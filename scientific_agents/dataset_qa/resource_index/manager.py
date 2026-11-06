"""Bounded, resumable directory traversal using the existing MCP transport."""
import asyncio
import json
import logging

from ..capabilities import profile
from ..contracts import QAError
from ..execution import Execution
from .model import DirectorySpec, IndexPolicy, source_identity
from .store import IndexStore, ROOT

log = logging.getLogger("flow.dataset_qa.index")


class ResourceIndex:
    def __init__(self, store, gateway, busy, policy=None):
        self.policy = policy or IndexPolicy()
        self.store = IndexStore(store.engine, store.lock, self.policy)
        self.gateway, self.busy = gateway, busy
        self.workers, self.wake, self.closed = [], asyncio.Event(), False
        self.changed = asyncio.Condition()
        self.revision = 0

    async def _notify(self):
        async with self.changed:
            self.revision += 1
            self.changed.notify_all()

    async def _wait(self, revision, timeout):
        async with self.changed:
            try:
                await asyncio.wait_for(self.changed.wait_for(lambda: self.revision!=revision or self.closed), timeout)
            except TimeoutError:
                pass  # Periodically re-read for work completed by another process.

    def sources(self):
        return {name: source_identity(server) for name, server in self.gateway.configured_servers().items()}

    def start(self):
        if not self.workers and not self.closed:
            self.workers = [asyncio.create_task(self._worker()) for _ in range(self.policy.workers)]

    async def close(self):
        self.closed = True
        await self._notify()
        for worker in self.workers:
            worker.cancel()
        await asyncio.gather(*self.workers, return_exceptions=True)
        self.workers.clear()

    async def observe(self, user, tool, arguments, data, dataset):
        if not profile(tool).directory or not Execution.reusable(tool):
            return None
        key = await asyncio.to_thread(self.store.observe, user, tool, self.sources()[tool.server], arguments, data, dataset)
        self.start()
        self.wake.set()
        await self._notify()
        return key

    async def _worker(self):
        while not self.closed:
            job = None
            try:
                claim = asyncio.create_task(asyncio.to_thread(self.store.claim, self.sources(), foreground=self.busy()))
                try:
                    job = await asyncio.shield(claim)
                except asyncio.CancelledError:
                    # A thread cannot be cancelled midway through acquisition.
                    # Wait for its transaction, then release its lease below.
                    job = await claim
                    raise
                if job is None:
                    self.wake.clear()
                    try:
                        await asyncio.wait_for(self.wake.wait(), self.policy.poll_seconds)
                    except TimeoutError:
                        pass
                    continue
                scope, node = job["scope"], job["node"]
                spec = DirectorySpec.model_validate_json(scope["descriptor"])
                args = json.loads(scope["arguments"])
                if node["key"]!=ROOT:
                    args[spec.parent] = json.loads(node["identity"])
                async with asyncio.timeout(min(self.policy.request_timeout, self.policy.lease_seconds/2)):
                    async with self.gateway.session() as tools:
                        if self.sources().get(scope["server"])!=scope["source"]:
                            raise QAError("source_changed", "目录来源已更新")
                        tool = next((tool for tool in await tools.tools(scope["server"]) if tool.name==scope["tool"]), None)
                        if tool is None or not Execution.reusable(tool) or profile(tool).directory!=spec:
                            raise QAError("invalid_schema", "目录能力已变化，请重新获取目录")
                        tools.include([tool])
                        _, output = await tools.call(tool.alias, args)
                        rows = spec.rows(output.data)
                await asyncio.to_thread(self.store.finish, job, rows)
            except asyncio.CancelledError:
                if job:
                    await asyncio.to_thread(self.store.release, job)
                raise
            except Exception as exc:
                code = getattr(exc, "code", "index_unavailable")
                if job:
                    try:
                        await asyncio.to_thread(self.store.finish, job, error=code, retry=isinstance(exc, TimeoutError) or
                            code in {"mcp_unavailable", "execution_unknown"})
                    except Exception:
                        # Lease expiry permits recovery after a database outage.
                        log.warning("Directory index receipt deferred")
                        await asyncio.sleep(self.policy.poll_seconds)
                log.warning("Directory index deferred: code=%s", code)
                if job is None:
                    await asyncio.sleep(self.policy.poll_seconds)
            finally:
                if job:
                    await self._notify()

    async def lookup(self, user, name, *, scope_id=None, parent=None, kind="file", refresh=False):
        sources = self.sources()
        query = dict(scope_id=scope_id, parent=parent, kind=kind)
        result = await asyncio.to_thread(self.store.lookup, user, sources, name, **query)
        if not result["scopes"]:
            return result
        targets = set(result["scopes"] if refresh else result["stale"])
        for key in targets:
            await asyncio.to_thread(self.store.refresh, user, key, sources, full=True)
        for item in result["items"]:
            if not item["fresh"] and item["scope"] not in targets:
                await asyncio.to_thread(self.store.refresh, user, item["scope"], sources, item["parent"])
        if refresh or targets or not result["complete"] or any(not item["fresh"] for item in result["items"]):
            # Prioritize an already queued lookup; do not reset failed nodes
            # repeatedly. Only an explicit refresh restarts failed work.
            for key in result["scopes"]:
                await asyncio.to_thread(self.store.prioritize, user, key, sources)
            self.start()
            self.wake.set()
            end = asyncio.get_running_loop().time()+self.policy.lookup_wait
            while not self.closed:
                revision = self.revision
                result = await asyncio.to_thread(self.store.lookup, user, sources, name, **query)
                if not result["pending"] or (result["complete"] and all(item["fresh"] for item in result["items"])):
                    break
                remaining = end-asyncio.get_running_loop().time()
                if remaining<=0:
                    break
                await self._wait(revision, min(self.policy.poll_seconds, remaining))
        return result
