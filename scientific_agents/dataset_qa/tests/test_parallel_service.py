"""Parallel remote reads keep durable receipts, budgets and partial outcomes."""
import asyncio
from dataclasses import replace
import json
import time
from types import SimpleNamespace

import pytest

from .assertions import assert_completed, assert_handled
from ..capabilities import OBJECT
from ..contracts import QAError
from ..service import DatasetQA
from .test_dataset_qa import action, collect, engine, remote, result_cards, session
from .test_decisions import BareDialogue, configured, goals, payload, seed, text


def finish(messages, definitions):
    return action("deliver_results") if definitions else text("The available results are shown.")


def read_goals():
    return goals({"description": "Inspect A", "tool": "inspect", "object": "candidate:1"},
        {"description": "Preview B", "tool": "preview", "object": "candidate:2"},
        calls=[remote("inspect", **{OBJECT: "candidate:1"}), remote("preview", **{OBJECT: "candidate:2"})])


def safe_backend():
    backend = configured()
    for definition in backend.catalog["data"][1:3]:
        definition.annotations = {"readOnlyHint": True, "idempotentHint": True}
    return backend


@pytest.mark.parametrize("parallel", [1, 2])
@pytest.mark.parametrize("failure_phase", [None, "authorization", "signing"])
def test_artifact_reads_keep_authorization_and_execution_context_in_both_dispatch_modes(engine, monkeypatch, parallel, failure_phase):
    monkeypatch.setenv("DATASET_QA_ARTIFACT_SIGNING_KEY", "parallel-read-test-key")
    if failure_phase == "signing":
        from .. import service as service_module
        original_metadata = service_module.execution_metadata
        def sign(user, request_id, arguments, seconds):
            if arguments["reference"] == "b":
                raise QAError("artifact_unavailable", "Signing service unavailable", 503)
            return original_metadata(user, request_id, arguments, seconds)
        monkeypatch.setattr(service_module, "execution_metadata", sign)

    async def run():
        backend, dialogue = safe_backend(), BareDialogue()
        for definition in backend.catalog["data"][1:3]:
            definition.annotations["destructiveHint"] = False
            definition.meta["piflow"]["qa"]["artifact"] = {
                "consume": "reference", "execution_context": True, "replay_safe": True}
        original, dispatched, authorized = backend.client, [], []
        active, peak = 0, 0

        def client(*args, **kwargs):
            connection = original(*args, **kwargs)
            execute = connection.call_tool

            async def call(name, arguments, **options):
                nonlocal active, peak
                if name not in {"inspect", "preview"}:
                    return await execute(name, arguments, **options)
                source = arguments["reference"]
                assert ("alice", "data", source) in authorized
                metadata = options.get("meta", {}).get("piflow_execution", {})
                assert metadata.get("user") == "alice"
                assert metadata.get("request_id") and metadata.get("signature")
                remaining = metadata["deadline"] - time.time()
                assert 0 < remaining <= service.gateway.limits.turn_timeout - service.gateway.limits.summary_timeout
                assert source != "b" or not failure_phase
                dispatched.append(source)
                active += 1
                peak = max(peak, active)
                try:
                    await asyncio.sleep(0.03)
                    return await execute(name, arguments, **options)
                finally:
                    active -= 1
            connection.call_tool = call
            return connection

        backend.client = client
        service = DatasetQA(engine, dialogue, backend.gateway())
        service.gateway.limits = replace(service.gateway.limits, max_parallel_reads=parallel)
        def authorize(user, server, source):
            authorized.append((user, server, source))
            if failure_phase == "authorization" and source == "b":
                raise QAError("artifact_unavailable", "Resource is not owned by this user", 403)
        monkeypatch.setattr(service.artifacts, "authorize", authorize)
        try:
            sid = session(service)
            await seed(service, dialogue, sid)
            dialogue.responses = [read_goals(), *[finish]*3]
            events = await collect(service, sid, "Inspect A and preview B", "artifact-reads")
            assert sorted(dispatched) == (["a"] if failure_phase else ["a", "b"])
            assert sorted(authorized) == [("alice", "data", "a"), ("alice", "data", "b")]
            assert peak == (parallel if not failure_phase else 1)
            if failure_phase:
                rejected = next(item for item in payload(service, sid, events)["operations"]
                    if item["capability"]["name"] == "preview")
                assert len(rejected["attempts"]) == 1
                assert rejected["attempts"][0]["dispatched"] is False
                assert not any(name == "preview" for _, name, _ in backend.calls)
        finally:
            await service.close()
    asyncio.run(run())


async def wait_until(predicate):
    async with asyncio.timeout(2):
        while not predicate():
            await asyncio.sleep(0.005)


def test_parallel_reads_reserve_before_dispatch_and_save_fast_result_before_slow_one(engine):
    async def run():
        backend, dialogue = safe_backend(), BareDialogue()
        original, started, release = backend.client, set(), asyncio.Event()
        service, sid = None, None

        def client(*args, **kwargs):
            connection = original(*args, **kwargs)
            execute = connection.call_tool

            async def call(name, arguments, **options):
                if name in {"inspect", "preview"}:
                    tid = service.store.session("alice", sid)["active_task_id"]
                    ledger = json.loads(service.store.task("alice", sid, tid)["payload"])
                    assert len(ledger["operations"])==2
                    assert all(item["state"]=="running" for item in ledger["operations"])
                    started.add(name)
                    await wait_until(lambda: len(started)==2)
                    if name=="inspect":
                        await release.wait()
                return await execute(name, arguments, **options)
            connection.call_tool = call
            return connection

        backend.client = client
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        job = None
        try:
            await seed(service, dialogue, sid)
            # One semantic declaration plus two reads exactly fills the budget.
            service.gateway.limits = replace(service.gateway.limits, max_calls=3)
            dialogue.responses = [read_goals(), *[finish]*3]
            job = asyncio.create_task(collect(service, sid, "Inspect A and preview B", "parallel"))
            await wait_until(lambda: len(started)==2)
            tid = service.store.session("alice", sid)["active_task_id"]
            await wait_until(lambda: len(service.store.results("alice", sid, tid))==1)
            ledger = json.loads(service.store.task("alice", sid, tid)["payload"])
            assert [item["state"] for item in ledger["operations"]]==["running", "succeeded"]
            release.set()
            values = await job
            assert_completed(service, None, values[-1])
            assert len(result_cards(values))==2
            ledger = payload(service, sid, values)
            assert all(len(item["attempts"])==1 and item["state"]=="succeeded" for item in ledger["operations"])
            assert [card["result_id"].rsplit(":", 1)[1] for card in result_cards(values)]==["0", "1"]
            assert len(backend.calls)==3
        finally:
            release.set()
            if job:
                await asyncio.gather(job, return_exceptions=True)
            await service.close()
    asyncio.run(run())


@pytest.mark.parametrize("kind", ["same_goal", "sampling", "budget"])
def test_nonindependent_or_unsafe_or_overbudget_work_does_not_overlap(engine, kind):
    async def run():
        backend, dialogue = safe_backend(), BareDialogue()
        backend.catalog["data"][0].annotations = {"readOnlyHint": True, "idempotentHint": True}
        original, active, peak = backend.client, 0, 0
        measuring = False

        def client(*args, **kwargs):
            connection = original(*args, **kwargs)
            execute = connection.call_tool

            async def call(name, arguments, **options):
                nonlocal active, peak
                if not measuring:
                    return await execute(name, arguments, **options)
                active += 1
                peak = max(peak, active)
                try:
                    await asyncio.sleep(0.01)
                    return await execute(name, arguments, **options)
                finally:
                    active -= 1
            connection.call_tool = call
            return connection

        backend.client = client
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            await seed(service, dialogue, sid)
            measuring = True
            if kind=="same_goal":
                request = goals({"description": "Find related resources", "tool": "search"},
                    calls=[remote("search", query="field one"), remote("search", query="field two")])
            elif kind=="sampling":
                request = goals({"description": "Sample A", "tool": "sample", "object": "candidate:1"},
                    {"description": "Sample B", "tool": "sample", "object": "candidate:2"},
                    calls=[remote("sample", count=1, **{OBJECT: "candidate:1"}),
                        remote("sample", count=1, **{OBJECT: "candidate:2"})])
            else:
                request = read_goals()
                service.gateway.limits = replace(service.gateway.limits, max_calls=2)
            dialogue.responses = [request, *[finish]*3]
            values = await collect(service, sid, "Process the requested datasets", kind)
            assert peak==1 and active==0
            assert len(backend.calls)==(2 if kind=="budget" else 3)
            if kind=="budget":
                assert_handled(service, None, values[-1], "step_limit")
                assert len(result_cards(values))==1
            else:
                assert_completed(service, None, values[-1])
        finally:
            await service.close()
    asyncio.run(run())


def test_one_parallel_failure_keeps_the_other_receipt_and_never_reexecutes_it(engine):
    async def run():
        backend, dialogue = safe_backend(), BareDialogue()
        original = backend.client

        def client(*args, **kwargs):
            connection = original(*args, **kwargs)
            execute = connection.call_tool

            async def call(name, arguments, **options):
                result = await execute(name, arguments, **options)
                if name=="preview":
                    return SimpleNamespace(is_error=True, content=[SimpleNamespace(type="text", text="Preview unavailable")])
                return result
            connection.call_tool = call
            return connection

        backend.client = client
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            await seed(service, dialogue, sid)
            dialogue.responses = [read_goals(), *[finish]*3]
            values = await collect(service, sid, "Inspect A and preview B", "one-failure")
            assert_handled(service, None, values[-1], "tool_failed")
            assert len(result_cards(values))==1 and len(backend.calls)==3
            ledger = payload(service, sid, values)
            assert [item["state"] for item in ledger["operations"]]==["succeeded", "failed"]
            assert all(len(item["attempts"])==1 for item in ledger["operations"])
            assert result_cards(values)[0]["result_id"]==ledger["operations"][0]["attempts"][0]["result_id"]
        finally:
            await service.close()
    asyncio.run(run())


@pytest.mark.parametrize("ending", ["timeout", "cancel"])
def test_interrupted_parallel_read_keeps_completed_artifact_and_joins_waiting_worker(engine, ending):
    async def run():
        backend, dialogue = safe_backend(), BareDialogue()
        original, blocked, exited = backend.client, asyncio.Event(), asyncio.Event()

        def client(*args, **kwargs):
            connection = original(*args, **kwargs)
            execute = connection.call_tool

            async def call(name, arguments, **options):
                if name=="preview":
                    blocked.set()
                    try:
                        await asyncio.Event().wait()
                    finally:
                        exited.set()
                return await execute(name, arguments, **options)
            connection.call_tool = call
            return connection

        backend.client = client
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        job = None
        try:
            await seed(service, dialogue, sid)
            if ending=="timeout":
                service.gateway.limits = replace(service.gateway.limits, turn_timeout=0.5)
            dialogue.responses = [read_goals(), *[finish]*3]
            job = asyncio.create_task(collect(service, sid, "Inspect A and preview B", ending))
            await asyncio.wait_for(blocked.wait(), 2)
            tid = service.store.session("alice", sid)["active_task_id"]
            await wait_until(lambda: len(service.store.results("alice", sid, tid))==1)
            if ending=="cancel":
                await service.cancel("alice", sid, tid)
            values = await asyncio.wait_for(job, 2)
            await asyncio.wait_for(exited.wait(), 2)
            assert len(result_cards(values))==1
            if ending=="cancel":
                assert values[-1]["status"]=="CANCELLED"
            else:
                assert_handled(service, sid, values[-1], "task_timeout")
            ledger = payload(service, sid, values)
            assert ledger["operations"][0]["state"]=="succeeded"
            assert ledger["operations"][1]["state"]=="unknown"
            assert len(ledger["operations"][0]["attempts"])==1
        finally:
            await service.close()
            if job:
                await asyncio.gather(job, return_exceptions=True)
    asyncio.run(run())
