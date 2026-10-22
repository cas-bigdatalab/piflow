"""Bounded remote reads with serialized, durable outcome collection."""
import asyncio

from .contracts import QAError


async def run_read_batch(calls, execute, persist, limit=4):
    """Run independent reads concurrently and persist each completed outcome.

    The caller determines which reads are safe to run independently. ``execute``
    performs remote I/O and returns its result, normally ``(tool, output)``.
    ``persist(call, result, error)`` owns all business-state changes and is awaited
    serially. An outcome enters the returned mapping only after persistence
    succeeds. A ``QAError`` from execution is an ordinary per-call failure;
    persistence errors, unexpected execution errors and cancellation abort the
    batch after every worker has been cancelled and joined.
    """
    if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
        raise ValueError("Parallel read limit must be a positive integer")
    calls = list(calls)
    ids = [call.get("id") for call in calls]
    if any(not isinstance(value, str) or not value for value in ids) or len(set(ids)) != len(ids):
        raise ValueError("Parallel calls require unique nonempty string IDs")
    semaphore = asyncio.Semaphore(limit)

    async def worker(call):
        async with semaphore:
            try:
                return call, await execute(call), None
            except QAError as error:
                return call, None, error

    tasks = [asyncio.create_task(worker(call)) for call in calls]
    outcomes = {}
    try:
        for completed in asyncio.as_completed(tasks):
            call, result, error = await completed
            await persist(call, result, error)
            outcomes[call["id"]] = (result, error)
        return outcomes
    finally:
        for task in tasks:
            if not task.done():
                task.cancel()
        # Retrieve every exception and wait for transport/context cleanup. Never
        # leave a worker writing or returning an unobserved result after exit.
        cleanup = asyncio.gather(*tasks, return_exceptions=True)
        cancellation = None
        while not cleanup.done():
            try:
                # A second cancellation must not cancel a worker's already
                # running asynchronous connection cleanup.
                await asyncio.shield(cleanup)
            except asyncio.CancelledError as error:
                cancellation = error
        if cancellation is not None:
            raise cancellation
