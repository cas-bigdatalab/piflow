"""Concurrency, persistence and cancellation contracts for parallel reads."""
import asyncio

import pytest

from ..contracts import QAError
from ..parallel import run_read_batch


def calls(count):
    return [{"id": f"call-{i}", "name": "inspect", "args": {"value": i}} for i in range(count)]


def test_read_batch_runs_in_parallel_and_persists_serially():
    async def run():
        started, persisted = set(), []
        barrier = asyncio.Event()
        persisting = 0

        async def execute(call):
            started.add(call["id"])
            if len(started) == 4:
                barrier.set()
            await asyncio.wait_for(barrier.wait(), timeout=1)
            return "tool", {"value": call["args"]["value"]}

        async def persist(call, result, error):
            nonlocal persisting
            persisting += 1
            assert persisting == 1
            await asyncio.sleep(0)
            persisted.append((call["id"], result, error))
            persisting -= 1

        outcomes = await run_read_batch(calls(4), execute, persist)
        assert set(outcomes) == started
        assert len(persisted) == 4
        for key, result, error in persisted:
            assert outcomes[key] == (result, error)
            assert error is None
    asyncio.run(run())


@pytest.mark.parametrize("limit", [1, 2, 4])
def test_read_batch_limits_active_remote_calls(limit):
    async def run():
        active, peak = 0, 0
        persisted = []

        async def execute(call):
            nonlocal active, peak
            active += 1
            peak = max(peak, active)
            try:
                await asyncio.sleep(0.005)
                return "tool", call["args"]
            finally:
                active -= 1

        async def persist(call, result, error):
            persisted.append(call["id"])

        outcomes = await run_read_batch(calls(7), execute, persist, limit=limit)
        assert peak == limit and active == 0
        assert len(outcomes) == len(persisted) == 7
    asyncio.run(run())


def test_read_batch_keeps_successes_when_one_tool_reports_failure():
    async def run():
        failure = QAError("tool_failed", "One service returned a failure", 502)
        persisted = {}

        async def execute(call):
            if call["id"] == "call-1":
                raise failure
            await asyncio.sleep(0)
            return "tool", call["args"]

        async def persist(call, result, error):
            persisted[call["id"]] = (result, error)

        outcomes = await run_read_batch(calls(3), execute, persist)
        assert outcomes == persisted
        assert outcomes["call-1"] == (None, failure)
        assert outcomes["call-0"] == (("tool", {"value": 0}), None)
        assert outcomes["call-2"] == (("tool", {"value": 2}), None)
    asyncio.run(run())


@pytest.mark.parametrize("failure_source", ["execute", "persist"])
def test_read_batch_unexpected_failure_cancels_and_joins_other_workers(failure_source):
    async def run():
        failure = RuntimeError("Unexpected execution or persistence fault")
        entered, cleaned, persisted = set(), set(), []
        barrier = asyncio.Event()

        async def execute(call):
            entered.add(call["id"])
            if len(entered) == 3:
                barrier.set()
            try:
                await barrier.wait()
                if call["id"] == "call-0":
                    if failure_source == "execute":
                        raise failure
                    return "tool", {"ready": True}
                await asyncio.Event().wait()
            finally:
                # Cleanup is asynchronous; the collector must join it too.
                await asyncio.sleep(0)
                cleaned.add(call["id"])

        async def persist(call, result, error):
            persisted.append(call["id"])
            raise failure

        with pytest.raises(RuntimeError) as caught:
            await asyncio.wait_for(run_read_batch(calls(3), execute, persist), timeout=1)
        assert caught.value is failure
        assert cleaned == entered == {"call-0", "call-1", "call-2"}
        assert persisted == (["call-0"] if failure_source == "persist" else [])
    asyncio.run(run())


@pytest.mark.parametrize("phase", ["execute", "persist"])
def test_read_batch_cancellation_cleans_active_and_waiting_workers(phase):
    async def run():
        entered, cleaned, persisted = set(), set(), []
        ready = asyncio.Event()

        async def execute(call):
            entered.add(call["id"])
            try:
                if phase == "persist" and call["id"] == "call-0":
                    return "tool", {"ready": True}
                if phase == "execute" and len(entered) == 2:
                    ready.set()
                await asyncio.Event().wait()
            finally:
                await asyncio.sleep(0)
                cleaned.add(call["id"])

        async def persist(call, result, error):
            ready.set()
            await asyncio.Event().wait()
            persisted.append(call["id"])

        batch = asyncio.create_task(run_read_batch(calls(6), execute, persist, limit=2))
        await asyncio.wait_for(ready.wait(), timeout=1)
        batch.cancel()
        with pytest.raises(asyncio.CancelledError):
            await batch
        assert entered == cleaned
        assert len(entered) < 6 and not persisted
    asyncio.run(run())


def test_read_batch_does_not_finish_until_result_has_been_persisted():
    async def run():
        persisting, release = asyncio.Event(), asyncio.Event()

        async def execute(call):
            return "tool", {"ready": True}

        async def persist(call, result, error):
            persisting.set()
            await release.wait()

        batch = asyncio.create_task(run_read_batch(calls(1), execute, persist))
        await asyncio.wait_for(persisting.wait(), timeout=1)
        assert not batch.done()
        release.set()
        assert await batch == {"call-0": (("tool", {"ready": True}), None)}
    asyncio.run(run())


@pytest.mark.parametrize("limit", [0, -1, True, 1.5])
def test_invalid_parallel_limit_is_rejected_before_execution(limit):
    async def run():
        async def untouched(*args):
            raise AssertionError("Validation must precede execution and persistence")

        with pytest.raises(ValueError):
            await run_read_batch(calls(2), untouched, untouched, limit=limit)
    asyncio.run(run())


def test_duplicate_ids_are_rejected_before_execution_and_empty_batch_is_valid():
    async def run():
        async def untouched(*args):
            raise AssertionError("No remote work expected")

        with pytest.raises(ValueError):
            await run_read_batch([*calls(1), *calls(1)], untouched, untouched)
        assert await run_read_batch([], untouched, untouched) == {}
    asyncio.run(run())


def test_repeated_cancellation_cannot_interrupt_transport_cleanup():
    async def run():
        started, cleaning, release, closed = (asyncio.Event() for _ in range(4))

        async def execute(call):
            started.set()
            try:
                await asyncio.Event().wait()
            finally:
                cleaning.set()
                await release.wait()
                closed.set()

        async def persist(*args):
            raise AssertionError("Cancelled execution cannot be persisted as success")

        batch = asyncio.create_task(run_read_batch(calls(1), execute, persist))
        await asyncio.wait_for(started.wait(), timeout=1)
        batch.cancel()
        await asyncio.wait_for(cleaning.wait(), timeout=1)
        batch.cancel()
        await asyncio.sleep(0)
        release.set()
        with pytest.raises(asyncio.CancelledError):
            await batch
        assert closed.is_set()
    asyncio.run(run())
