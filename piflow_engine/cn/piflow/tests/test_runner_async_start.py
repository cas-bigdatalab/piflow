from __future__ import annotations

import threading
import time
from pathlib import Path

import pytest

from cn.piflow.core.artifact import FileArtifact
from cn.piflow.core.flow import FlowImpl
from cn.piflow.core.path import Path as FlowPath
from cn.piflow.core.runner import Runner
from cn.piflow.core.runtime_context import JobContext, ProcessContext
from cn.piflow.core.stop import ConfigurableStop
from cn.piflow.core.stream import JobInputStream, JobOutputStream
from cn.piflow.engine.local.file_save_stop import FileSaveStop
from cn.piflow.runtime import RunStatus, RunTrackingListener
from cn.piflow.runtime.run_store import RunStore


class _BlockingSourceStop(ConfigurableStop):
    def __init__(self, entered: threading.Event, release: threading.Event) -> None:
        super().__init__()
        self.entered = entered
        self.release = release

    def set_properties(self, properties: dict[str, object]) -> None:
        return None

    def initialize(self, ctx: ProcessContext) -> None:
        return None

    def perform(
        self,
        inputs: JobInputStream,
        outputs: JobOutputStream,
        ctx: JobContext,
    ) -> None:
        self.entered.set()
        self.release.wait(timeout=2)
        outputs.write("ok")


class _MemoryRunStore(RunStore):
    def __init__(self) -> None:
        self.flow_statuses: list[str] = []
        self.stop_statuses: list[str] = []
        self.final_output_paths: list[str] = []

    def create_flow_run(
        self,
        *,
        process_id: str,
        flow_uuid: str,
        flow_name: str,
        status: str,
        total_stop_count: int,
        workspace_path: str,
        log_path: str = "",
    ):
        self.flow_statuses.append(status)
        return 1

    def update_flow_run(
        self,
        *,
        process_id: str,
        status: str | None = None,
        progress: float | None = None,
        success_stop_count: int | None = None,
        failed_stop_count: int | None = None,
        skipped_stop_count: int | None = None,
        error_message: str | None = None,
        finished: bool = False,
    ) -> None:
        if status is not None:
            self.flow_statuses.append(status)

    def create_stop_job_run(
        self,
        *,
        process_id: str,
        job_id: str,
        stop_name: str,
        status: str,
        stop_uuid: str = "",
        bundle: str = "",
        workspace_path: str = "",
        log_path: str = "",
        stdout_log_path: str = "",
        stderr_log_path: str = "",
        final_output_path: str = "",
    ):
        self.stop_statuses.append(status)
        if final_output_path:
            self.final_output_paths.append(final_output_path)
        return 1

    def update_stop_job_run(
        self,
        *,
        process_id: str,
        job_id: str,
        status: str,
        input_ports: list[str] | None = None,
        output_ports: list[str] | None = None,
        stdout_log_path: str | None = None,
        stderr_log_path: str | None = None,
        final_output_path: str | None = None,
        error_message: str | None = None,
        finished: bool = False,
    ) -> None:
        self.stop_statuses.append(status)
        if final_output_path:
            self.final_output_paths.append(final_output_path)


class _SourceFileStop(ConfigurableStop):
    def __init__(self, source_path: Path) -> None:
        super().__init__()
        self.source_path = source_path

    def set_properties(self, properties: dict[str, object]) -> None:
        return None

    def initialize(self, ctx: ProcessContext) -> None:
        return None

    def perform(
        self,
        inputs: JobInputStream,
        outputs: JobOutputStream,
        ctx: JobContext,
    ) -> None:
        outputs.write(FileArtifact(path=str(self.source_path)))


def test_runner_start_returns_before_flow_finishes() -> None:
    entered = threading.Event()
    release = threading.Event()
    flow = FlowImpl(name="demo", uuid="flow-1")
    flow.add_stop("source", _BlockingSourceStop(entered, release))

    runner = Runner.create()
    started_at = time.monotonic()
    process = runner.start(flow)
    elapsed = time.monotonic() - started_at

    assert process.pid().startswith("process_")
    assert elapsed < 0.5

    assert entered.wait(timeout=1)
    release.set()
    process.await_termination(timeout=2)


def test_run_tracking_listener_records_pending_then_running_then_success() -> None:
    entered = threading.Event()
    release = threading.Event()
    store = _MemoryRunStore()
    runner = Runner.create()
    runner.add_listener(RunTrackingListener(run_store=store))

    flow = FlowImpl(name="demo", uuid="flow-1")
    flow.add_stop("source", _BlockingSourceStop(entered, release))

    process = runner.start(flow)
    assert store.flow_statuses[:2] == [RunStatus.PENDING, RunStatus.RUNNING]

    assert entered.wait(timeout=1)
    release.set()
    process.await_termination(timeout=2)

    assert store.flow_statuses[-1] == RunStatus.SUCCESS
    assert store.stop_statuses[0] == RunStatus.PENDING
    assert RunStatus.RUNNING in store.stop_statuses
    assert RunStatus.SUCCESS in store.stop_statuses


def test_file_save_stop_records_final_output_path(tmp_path: Path) -> None:
    source_path = tmp_path / "input.txt"
    source_path.write_text("hello", encoding="utf-8")
    target_path = tmp_path / "nested" / "output.txt"

    store = _MemoryRunStore()
    runner = Runner.create()
    runner.add_listener(RunTrackingListener(run_store=store))

    flow = FlowImpl(name="demo", uuid="flow-1")
    flow.add_stop("source", _SourceFileStop(source_path))
    save_stop = FileSaveStop()
    save_stop.set_properties(
        {
            "absolute_path": str(target_path),
            "overwrite": True,
        }
    )
    flow.add_stop(
        "save",
        save_stop,
    )
    flow.add_path(FlowPath.from_("source").to("save"))

    process = runner.start(flow)
    process.await_termination(timeout=2)

    assert target_path.exists()
    assert str(target_path) in store.final_output_paths


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
