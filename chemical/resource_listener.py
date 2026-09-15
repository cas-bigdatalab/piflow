from __future__ import annotations

from threading import RLock
from typing import Any

from piflow_engine.cn.piflow.core.runner_listener import RunnerListener
from piflow_engine.cn.piflow.core.runtime_context import JobContext, ProcessContext

from .resource_tracker import ChemicalResourceTracker
from .runtime_keys import (
    CHEMICAL_RESOURCE_RESERVATION_KEY,
    CHEMICAL_RUNTIME_METADATA_KEY,
)


class ChemicalResourceTrackingListener(RunnerListener):
    """Track local and remote Chemical software-dependent stops."""

    def __init__(self, tracker: ChemicalResourceTracker | None = None) -> None:
        self._tracker = tracker or ChemicalResourceTracker()
        self._active: dict[tuple[str, str], dict[str, Any]] = {}
        self._lock = RLock()

    def on_process_submitted(self, ctx: ProcessContext) -> None:
        return None

    def on_process_started(self, ctx: ProcessContext) -> None:
        return None

    def on_process_completed(self, ctx: ProcessContext) -> None:
        return None

    def on_process_failed(self, ctx: ProcessContext, error: Exception) -> None:
        return None

    def on_process_aborted(self, ctx: ProcessContext) -> None:
        # ProcessImpl may report abort before an in-flight stop returns. The
        # active stop releases itself on completion or failure.
        return None

    def on_job_initialized(self, ctx: JobContext) -> None:
        stop = ctx.get_stop_job().get_stop()
        metadata = getattr(stop, "piflow_runtime_metadata", None)
        if metadata:
            ctx.put(CHEMICAL_RUNTIME_METADATA_KEY, dict(metadata))

    def on_job_started(self, ctx: JobContext) -> None:
        metadata = ctx.get(CHEMICAL_RUNTIME_METADATA_KEY, None)
        if not metadata:
            return

        bindings = tuple(
            (str(binding[0]), str(binding[1]))
            for binding in (metadata.get("resource_bindings") or ())
            if isinstance(binding, (list, tuple)) and len(binding) == 2
        )
        if not bindings:
            return

        self._tracker.reserve(bindings=bindings)
        with self._lock:
            self._active[self._job_key(ctx)] = {
                "bindings": bindings,
            }
        ctx.put(
            CHEMICAL_RESOURCE_RESERVATION_KEY,
            {"bindings": bindings},
        )

    def on_job_completed(self, ctx: JobContext) -> None:
        self._release(ctx)

    def on_job_failed(self, ctx: JobContext, error: Exception) -> None:
        self._release(ctx)

    def _release(self, ctx: JobContext) -> None:
        with self._lock:
            reservation = self._active.pop(self._job_key(ctx), None)
        if reservation is not None:
            self._tracker.release(**reservation)

    @staticmethod
    def _job_key(ctx: JobContext) -> tuple[str, str]:
        process_id = ctx.get_process_context().get_process().pid()
        job_id = ctx.get_stop_job().jid()
        return str(process_id), str(job_id)
