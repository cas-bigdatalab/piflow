from __future__ import annotations

import logging
import threading
import uuid
from datetime import datetime, timezone
from typing import Protocol

from runtime.schedule.models import ScheduleJob, ScheduleRun
from runtime.schedule.repository import (
    claim_due_jobs as repository_claim_due_jobs,
    mark_schedule_run_failed,
    mark_schedule_run_submitted,
)

log = logging.getLogger("flow.schedule")


class ScheduleDispatcher(Protocol):
    def dispatch(self, job: ScheduleJob, run: ScheduleRun) -> str:
        """Dispatch one claimed schedule run and return its process identifier."""


class FakeDispatcher:
    """A stage 4 dispatcher that records triggers without running a DAG."""

    def __init__(self) -> None:
        self.dispatched: list[tuple[str, str]] = []

    def dispatch(self, job: ScheduleJob, run: ScheduleRun) -> str:
        process_id = f"fake-{uuid.uuid4().hex}"
        self.dispatched.append((job.schedule_job_id, run.schedule_run_id))
        return process_id


class ScheduleDaemon:
    def __init__(
        self,
        *,
        dispatcher: ScheduleDispatcher | None = None,
        poll_interval_seconds: float = 1.0,
        batch_size: int = 100,
    ) -> None:
        if poll_interval_seconds <= 0:
            raise ValueError("poll_interval_seconds must be > 0")
        if batch_size <= 0:
            raise ValueError("batch_size must be > 0")

        self.dispatcher = dispatcher or FakeDispatcher()
        self.poll_interval_seconds = poll_interval_seconds
        self.batch_size = batch_size
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self) -> None:
        if self.is_running:
            return

        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run,
            name="piflow-schedule-daemon",
            daemon=True,
        )
        self._thread.start()

    def stop(self, timeout: float = 10.0) -> None:
        self._stop_event.set()
        thread = self._thread
        if thread is not None and thread is not threading.current_thread():
            thread.join(timeout=timeout)
        self._thread = None

    def _run(self) -> None:
        while not self._stop_event.is_set():
            try:
                self.tick()
            except Exception:
                log.exception("schedule daemon tick failed")
            self._stop_event.wait(self.poll_interval_seconds)

    def tick(self, *, now: datetime | None = None) -> list[ScheduleRun]:
        tick_time = now or datetime.now(timezone.utc)
        claimed = self.claim_due_jobs(now=tick_time)
        submitted: list[ScheduleRun] = []

        for job, run in claimed:
            result = self.fire_job(job, run)
            if result is not None:
                submitted.append(result)

        return submitted

    def claim_due_jobs(
        self,
        *,
        now: datetime,
    ) -> list[tuple[ScheduleJob, ScheduleRun]]:
        return repository_claim_due_jobs(now=now, limit=self.batch_size)

    def fire_job(self, job: ScheduleJob, run: ScheduleRun) -> ScheduleRun | None:
        try:
            process_id = self.dispatcher.dispatch(job, run)
            return mark_schedule_run_submitted(
                run.schedule_run_id,
                process_id=process_id,
            )
        except Exception as exc:
            log.exception(
                "failed to dispatch schedule run %s",
                run.schedule_run_id,
            )
            try:
                mark_schedule_run_failed(
                    run.schedule_run_id,
                    error_message=str(exc),
                )
            except Exception:
                log.exception(
                    "failed to mark schedule run %s as failed",
                    run.schedule_run_id,
                )
            return None
