from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from piflow_engine.cn.piflow.core.artifact import Artifact, FileArtifact
from piflow_engine.cn.piflow.core.runner_listener import RunnerListener
from piflow_engine.cn.piflow.core.runtime_context import JobContext, ProcessContext
from piflow_engine.cn.piflow.core.runtime_keys import (
    RUN_CONTEXT_FINAL_OUTPUT_PATH,
    RUN_CONTEXT_STDERR_LOG_PATH,
    RUN_CONTEXT_STDOUT_LOG_PATH,
)
from piflow_engine.cn.piflow.core.stream import JobInputStream, JobOutputStream
from piflow_engine.cn.piflow.runtime.logging import RunLogger, get_logger
from piflow_engine.cn.piflow.runtime.run_status import RunEvent, RunStatus
from piflow_engine.cn.piflow.runtime.run_store import RunStore


@dataclass
class _FlowRunState:
    total: int
    success: int = 0
    failed: int = 0
    skipped: int = 0

    @property
    def progress(self) -> float:
        if self.total <= 0:
            return 1.0
        return min((self.success + self.failed + self.skipped) / self.total, 1.0)


class RunTrackingListener(RunnerListener):
    def __init__(
        self,
        *,
        run_store: RunStore,
        run_logger: RunLogger | None = None,
    ) -> None:
        self._run_store = run_store
        self._run_logger = run_logger
        self._logger = get_logger(__name__)
        self._states: dict[str, _FlowRunState] = {}

    def on_process_submitted(self, ctx: ProcessContext) -> None:
        def action() -> None:
            process_id = ctx.get_process().pid()
            flow = ctx.get_flow()
            total = len(flow.get_stop_names())
            self._states[process_id] = _FlowRunState(total=total)
            workspace_path = self._workspace_path(process_id)

            self._run_store.create_flow_run(
                process_id=process_id,
                flow_uuid=str(getattr(flow, "uuid", "")),
                flow_name=str(getattr(flow, "name", "")),
                status=RunStatus.PENDING,
                total_stop_count=total,
                workspace_path=workspace_path,
                log_path=self._flow_log_path(process_id),
            )
            self._log_flow(
                process_id,
                RunEvent.FLOW_SUBMITTED,
                payload={"flow_name": getattr(flow, "name", ""), "total": total},
            )

        self._safe(action, "failed to track process submission")

    def on_process_started(self, ctx: ProcessContext) -> None:
        def action() -> None:
            process_id = ctx.get_process().pid()
            self._run_store.update_flow_run(
                process_id=process_id,
                status=RunStatus.RUNNING,
            )
            self._log_flow(
                process_id,
                RunEvent.FLOW_STARTED,
            )

        self._safe(action, "failed to track process start")

    def on_process_completed(self, ctx: ProcessContext) -> None:
        def action() -> None:
            process_id = ctx.get_process().pid()
            state = self._state(process_id)
            self._run_store.update_flow_run(
                process_id=process_id,
                status=RunStatus.SUCCESS,
                progress=1.0,
                success_stop_count=state.success,
                failed_stop_count=state.failed,
                skipped_stop_count=state.skipped,
                finished=True,
            )
            self._log_flow(process_id, RunEvent.FLOW_COMPLETED)

        self._safe(action, "failed to track process completion")

    def on_process_failed(self, ctx: ProcessContext, error: Exception) -> None:
        def action() -> None:
            process_id = ctx.get_process().pid()
            state = self._state(process_id)
            self._run_store.update_flow_run(
                process_id=process_id,
                status=RunStatus.FAILED,
                progress=state.progress,
                success_stop_count=state.success,
                failed_stop_count=state.failed,
                skipped_stop_count=state.skipped,
                error_message=str(error),
                finished=True,
            )
            self._log_flow(
                process_id,
                RunEvent.FLOW_FAILED,
                level="ERROR",
                message=str(error),
            )

        self._safe(action, "failed to track process failure")

    def on_process_aborted(self, ctx: ProcessContext) -> None:
        def action() -> None:
            process_id = ctx.get_process().pid()
            self._run_store.update_flow_run(
                process_id=process_id,
                status=RunStatus.CANCELLED,
                finished=True,
            )
            self._log_flow(process_id, RunEvent.FLOW_ABORTED, level="WARNING")

        self._safe(action, "failed to track process abort")

    def on_job_initialized(self, ctx: JobContext) -> None:
        def action() -> None:
            process_id = ctx.get_process_context().get_process().pid()
            stop_job = ctx.get_stop_job()
            metadata = self._stop_metadata(ctx)
            self._run_store.create_stop_job_run(
                process_id=process_id,
                job_id=stop_job.jid(),
                stop_name=stop_job.get_stop_name(),
                status=RunStatus.PENDING,
                stop_uuid=metadata["stop_uuid"],
                bundle=metadata["bundle"],
                workspace_path=self._workspace_path(process_id),
                log_path=self._stop_log_path(ctx),
                stdout_log_path="",
                stderr_log_path="",
            )
            self._log_stop(ctx, RunEvent.STOP_INITIALIZED, payload=metadata)

        self._safe(action, "failed to track job initialization")

    def on_job_started(self, ctx: JobContext) -> None:
        def action() -> None:
            process_id = ctx.get_process_context().get_process().pid()
            stop_job = ctx.get_stop_job()
            self._run_store.update_stop_job_run(
                process_id=process_id,
                job_id=stop_job.jid(),
                status=RunStatus.RUNNING,
                input_ports=ctx.get_input_stream().ports(),
            )
            self._log_stop(
                ctx,
                RunEvent.STOP_STARTED,
                payload={
                    "input_ports": ctx.get_input_stream().ports(),
                    "inputs": self._input_snapshot(ctx.get_input_stream()),
                },
            )

        self._safe(action, "failed to track job start")

    def on_job_completed(self, ctx: JobContext) -> None:
        def action() -> None:
            process_id = ctx.get_process_context().get_process().pid()
            stop_job = ctx.get_stop_job()
            state = self._state(process_id)
            state.success += 1
            self._run_store.update_stop_job_run(
                process_id=process_id,
                job_id=stop_job.jid(),
                status=RunStatus.SUCCESS,
                input_ports=ctx.get_input_stream().ports(),
                output_ports=ctx.get_output_stream().ports(),
                stdout_log_path=self._context_value(ctx, RUN_CONTEXT_STDOUT_LOG_PATH),
                stderr_log_path=self._context_value(ctx, RUN_CONTEXT_STDERR_LOG_PATH),
                final_output_path=self._context_value(ctx, RUN_CONTEXT_FINAL_OUTPUT_PATH),
                finished=True,
            )
            self._run_store.update_flow_run(
                process_id=process_id,
                progress=state.progress,
                success_stop_count=state.success,
                failed_stop_count=state.failed,
                skipped_stop_count=state.skipped,
            )
            self._log_stop(
                ctx,
                RunEvent.STOP_COMPLETED,
                payload={
                    "input_ports": ctx.get_input_stream().ports(),
                    "output_ports": ctx.get_output_stream().ports(),
                    "inputs": self._input_snapshot(ctx.get_input_stream()),
                    "outputs": self._output_snapshot(ctx.get_output_stream()),
                    "progress": state.progress,
                },
            )

        self._safe(action, "failed to track job completion")

    def on_job_failed(self, ctx: JobContext, error: Exception) -> None:
        def action() -> None:
            process_id = ctx.get_process_context().get_process().pid()
            stop_job = ctx.get_stop_job()
            state = self._state(process_id)
            state.failed += 1
            self._run_store.update_stop_job_run(
                process_id=process_id,
                job_id=stop_job.jid(),
                status=RunStatus.FAILED,
                input_ports=ctx.get_input_stream().ports(),
                output_ports=ctx.get_output_stream().ports(),
                stdout_log_path=self._context_value(ctx, RUN_CONTEXT_STDOUT_LOG_PATH),
                stderr_log_path=self._context_value(ctx, RUN_CONTEXT_STDERR_LOG_PATH),
                final_output_path=self._context_value(ctx, RUN_CONTEXT_FINAL_OUTPUT_PATH),
                error_message=str(error),
                finished=True,
            )
            self._run_store.update_flow_run(
                process_id=process_id,
                status=RunStatus.FAILED,
                progress=state.progress,
                success_stop_count=state.success,
                failed_stop_count=state.failed,
                skipped_stop_count=state.skipped,
                error_message=str(error),
            )
            self._log_stop(
                ctx,
                RunEvent.STOP_FAILED,
                level="ERROR",
                message=str(error),
                payload={
                    "input_ports": ctx.get_input_stream().ports(),
                    "output_ports": ctx.get_output_stream().ports(),
                    "inputs": self._input_snapshot(ctx.get_input_stream()),
                    "outputs": self._output_snapshot(ctx.get_output_stream()),
                    "progress": state.progress,
                },
            )

        self._safe(action, "failed to track job failure")

    def _state(self, process_id: str) -> _FlowRunState:
        return self._states.setdefault(process_id, _FlowRunState(total=0))

    def _workspace_path(self, process_id: str) -> str:
        if self._run_logger is None:
            return ""
        return str((Path(self._run_logger.workspace_root) / process_id).resolve())

    def _flow_log_path(self, process_id: str) -> str:
        if self._run_logger is None:
            return ""
        return str(self._run_logger.flow_log_path(process_id).resolve())

    def _stop_log_path(self, ctx: JobContext) -> str:
        if self._run_logger is None:
            return ""
        process_id = ctx.get_process_context().get_process().pid()
        stop_name = ctx.get_stop_job().get_stop_name()
        return str(self._run_logger.stop_log_path(process_id, stop_name).resolve())

    def _log_flow(
        self,
        process_id: str,
        event: str,
        *,
        level: str = "INFO",
        message: str = "",
        payload: dict | None = None,
    ) -> None:
        self._log_system_event(
            level,
            event,
            message,
            process_id=process_id,
            payload=payload,
        )
        if self._run_logger is not None:
            self._run_logger.log_flow_event(
                process_id,
                event,
                level=level,
                message=message,
                payload=payload,
            )

    def _log_stop(
        self,
        ctx: JobContext,
        event: str,
        *,
        level: str = "INFO",
        message: str = "",
        payload: dict | None = None,
    ) -> None:
        process_id = ctx.get_process_context().get_process().pid()
        stop_job = ctx.get_stop_job()
        self._log_system_event(
            level,
            event,
            message,
            process_id=process_id,
            job_id=stop_job.jid(),
            stop_name=stop_job.get_stop_name(),
            payload=payload,
        )
        if self._run_logger is None:
            return
        self._run_logger.log_stop_event(
            process_id,
            stop_job.get_stop_name(),
            event,
            job_id=stop_job.jid(),
            level=level,
            message=message,
            payload=payload,
        )

    def _safe(self, action: Callable[[], None], message: str) -> None:
        try:
            action()
        except Exception:
            self._logger.exception(message)

    def _log_system_event(
        self,
        level: str,
        event: str,
        message: str,
        **fields: Any,
    ) -> None:
        level_no = getattr(logging, level.upper(), logging.INFO)
        details = " ".join(
            f"{key}={value}"
            for key, value in fields.items()
            if value not in ("", None, {})
        )
        if message:
            self._logger.log(level_no, "%s %s message=%s", event, details, message)
        else:
            self._logger.log(level_no, "%s %s", event, details)

    def _stop_metadata(self, ctx: JobContext) -> dict[str, str]:
        stop = ctx.get_stop_job().get_stop()
        return {
            "stop_uuid": str(getattr(stop, "piflow_stop_uuid", "")),
            "stop_name": str(getattr(stop, "piflow_stop_name", "")),
            "bundle": str(getattr(stop, "piflow_bundle", "")),
        }

    def _input_snapshot(self, stream: JobInputStream) -> dict[str, dict[str, Any]]:
        return self._stream_snapshot(stream)

    def _output_snapshot(self, stream: JobOutputStream) -> dict[str, dict[str, Any]]:
        return self._stream_snapshot(stream)

    def _stream_snapshot(
        self,
        stream: JobInputStream | JobOutputStream,
    ) -> dict[str, dict[str, Any]]:
        snapshot: dict[str, dict[str, Any]] = {}
        for port in stream.ports():
            try:
                artifact = (
                    stream.read(port)
                    if isinstance(stream, JobInputStream)
                    else stream.get_artifact(port)
                )
                snapshot[port] = self._artifact_snapshot(artifact)
            except Exception as error:
                snapshot[port] = {"error": str(error)}
        return snapshot

    def _artifact_snapshot(self, artifact: Artifact) -> dict[str, Any]:
        data: dict[str, Any] = {
            "type": artifact.type,
            "metadata": self._json_safe(artifact.metadata),
        }
        if isinstance(artifact, FileArtifact):
            data["path"] = artifact.path
        else:
            data["value"] = self._json_safe(artifact.value)
        return data

    def _json_safe(self, value: Any) -> Any:
        if value is None or isinstance(value, (str, int, float, bool)):
            return value
        if isinstance(value, Path):
            return str(value)
        if isinstance(value, dict):
            return {str(key): self._json_safe(item) for key, item in value.items()}
        if isinstance(value, (list, tuple, set)):
            return [self._json_safe(item) for item in value]
        return str(value)

    def _context_value(self, ctx: JobContext, key: str) -> str:
        return str(ctx.get(key, "") or "")
