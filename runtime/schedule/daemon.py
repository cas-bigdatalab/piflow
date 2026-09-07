from __future__ import annotations

import logging
import threading
import uuid
from datetime import datetime, timezone
from typing import Protocol

from runtime.schedule.constants import ScheduleRunStatus
from runtime.schedule.models import ScheduleJob, ScheduleRun
from runtime.schedule.repository import (
    claim_due_jobs as repository_claim_due_jobs,
    list_submitted_runs,
    mark_run_completed,
    mark_run_dispatching,
    mark_schedule_run_failed,
    mark_schedule_run_submitted,
    recover_expired_dispatching_runs,
)
from services.dag_runtime_service import run_dag_task

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


class PiflowDispatcher:
    """默认 dispatcher：复用 run_dag_task 链路提交 DAG。"""

    def dispatch(self, job: ScheduleJob, run: ScheduleRun) -> str:
        result = run_dag_task(create_user_id=job.owner_id, dag_task_id=job.dag_task_id)
        return result["process_id"]


class ScheduleDaemon:
    def __init__(
        self,
        *,
        dispatcher: ScheduleDispatcher | None = None,
        poll_interval_seconds: float = 1.0,
        batch_size: int = 100,
        sync_interval_ticks: int = 10,
    ) -> None:
        if poll_interval_seconds <= 0:
            raise ValueError("poll_interval_seconds must be > 0")
        if batch_size <= 0:
            raise ValueError("batch_size must be > 0")

        self.dispatcher = dispatcher or PiflowDispatcher()
        self.poll_interval_seconds = poll_interval_seconds
        self.batch_size = batch_size
        self.sync_interval_ticks = sync_interval_ticks
        self._instance_id = uuid.uuid4().hex
        self._tick_count = 0
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
        log.info(
            "schedule daemon started (instance=%s, poll=%ss, dispatcher=%s)",
            self._instance_id,
            self.poll_interval_seconds,
            type(self.dispatcher).__name__,
        )

    def stop(self, timeout: float = 10.0) -> None:
        self._stop_event.set()
        thread = self._thread
        if thread is not None and thread is not threading.current_thread():
            thread.join(timeout=timeout)
        self._thread = None

    def _run(self) -> None:
        # 启动恢复：租约过期的 DISPATCHING → LOST
        try:
            now = datetime.now(timezone.utc)
            recovered = recover_expired_dispatching_runs(now=now)
            if recovered:
                log.info("recovered %d expired dispatching runs on startup", recovered)
        except Exception:
            log.exception("failed to recover expired dispatching runs on startup")

        while not self._stop_event.is_set():
            try:
                self.tick()
            except Exception:
                log.exception("schedule daemon tick failed")
            self._stop_event.wait(self.poll_interval_seconds)

    def tick(self, *, now: datetime | None = None) -> list[ScheduleRun]:
        tick_time = now or datetime.now(timezone.utc)
        self._tick_count += 1

        claimed = self.claim_due_jobs(now=tick_time)
        if claimed:
            log.info("schedule tick claimed %d due job(s)", len(claimed))
        submitted: list[ScheduleRun] = []

        for job, run in claimed:
            result = self.fire_job(job, run)
            if result is not None:
                submitted.append(result)

        # 低频同步：回写 SUBMITTED run 的终态
        if self._tick_count % self.sync_interval_ticks == 0:
            try:
                self.sync_submitted_runs()
            except Exception:
                log.exception("failed to sync submitted runs")

        return submitted

    def claim_due_jobs(
        self,
        *,
        now: datetime,
    ) -> list[tuple[ScheduleJob, ScheduleRun]]:
        return repository_claim_due_jobs(now=now, limit=self.batch_size)

    def fire_job(self, job: ScheduleJob, run: ScheduleRun) -> ScheduleRun | None:
        # 阶段1：PENDING → DISPATCHING（先占位，防止重启时 DAG 在跑但 run 未标记）
        try:
            dispatching = mark_run_dispatching(
                run.schedule_run_id,
                owner_id=self._instance_id,
            )
            if dispatching is None:
                return None
        except Exception:
            log.exception(
                "failed to mark schedule run %s as dispatching",
                run.schedule_run_id,
            )
            return None

        # 阶段2：调用 dispatcher 提交 DAG
        try:
            process_id = self.dispatcher.dispatch(job, run)
            log.info(
                "dispatched schedule run %s (job=%s, process_id=%s)",
                run.schedule_run_id,
                job.schedule_name,
                process_id,
            )
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

    def sync_submitted_runs(self, *, batch_size: int = 50) -> int:
        """低频同步：查 SUBMITTED 的 run，查 piflow 状态，回写终态。"""
        from runtime.piflow_run_query import get_piflow_run_progress

        runs = list_submitted_runs(limit=batch_size)
        completed = 0
        for run in runs:
            if run.process_id is None:
                continue
            try:
                piflow = get_piflow_run_progress(run.process_id)
            except Exception:
                log.debug(
                    "failed to query piflow progress for run %s (process %s)",
                    run.schedule_run_id,
                    run.process_id,
                )
                continue
            if piflow is None:
                continue

            piflow_status = piflow.get("status")
            if piflow_status == "SUCCESS":
                mark_run_completed(
                    run.schedule_run_id,
                    status=ScheduleRunStatus.SUCCESS,
                )
                completed += 1
            elif piflow_status == "FAILED":
                mark_run_completed(
                    run.schedule_run_id,
                    status=ScheduleRunStatus.FAILED,
                    error_message=piflow.get("error_message"),
                )
                completed += 1
            elif piflow_status in ("ABORTED", "CANCELLED"):
                mark_run_completed(
                    run.schedule_run_id,
                    status=ScheduleRunStatus.CANCELLED,
                    error_message=piflow.get("error_message"),
                )
                completed += 1
        return completed
