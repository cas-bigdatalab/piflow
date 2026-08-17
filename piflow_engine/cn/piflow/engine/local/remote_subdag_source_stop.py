from __future__ import annotations

import json
import time
import uuid
from pathlib import Path
from typing import Any, Protocol

from piflow_engine.cn.piflow.core.artifact import FileArtifact
from piflow_engine.cn.piflow.core.runtime_context import JobContext, ProcessContext
from piflow_engine.cn.piflow.core.stop import ConfigurableStop
from piflow_engine.cn.piflow.core.stream import JobInputStream, JobOutputStream
from piflow_engine.cn.piflow.engine.local.constants import RUNNER_CONTEXT_WORKSPACE_ROOT
from piflow_engine.cn.piflow.runtime.logging.path_utils import safe_name


class RemoteExecutionGateway(Protocol):
    def submit_dag(self, dag_definition_json: str): ...

    def get_run_status(self, run_id: str): ...

    def get_run_result_meta(
        self,
        *,
        run_id: str,
        result_node_id: str = "",
        result_output_name: str = "",
    ): ...

    def download_result(
        self,
        *,
        run_id: str,
        result_node_id: str = "",
        result_output_name: str = "",
        target_path: str | Path,
    ) -> str: ...

    def close(self) -> None: ...


OUTPUT_PORT = "output"
DEFAULT_WAIT_TIMEOUT_SECONDS = 3600
POLL_INTERVAL_SECONDS = 1.0


class RemoteSubDagSourceStop(ConfigurableStop):
    author_email = ""
    description = (
        "Scheduler-internal synthetic source stop that submits a remote sub-DAG "
        "and exposes its default final result as a FileArtifact."
    )
    inport_list: list[str] = []
    outport_list = [OUTPUT_PORT]
    is_data_source = True

    client_factory = None

    def __init__(self) -> None:
        super().__init__()
        self.remote_grpc_target = ""
        self.subdag_definition_json = ""
        self.result_node_id = ""
        self.result_output_name = ""
        self.wait_timeout_seconds = DEFAULT_WAIT_TIMEOUT_SECONDS
        self._workspace_root: Path | None = None

    def set_properties(self, properties: dict[str, Any]) -> None:
        self.remote_grpc_target = _require_non_empty_string(
            properties.get("remote_grpc_target", ""),
            name="remote_grpc_target",
        )
        self.subdag_definition_json = _normalize_json(
            properties.get("subdag_definition_json", ""),
            name="subdag_definition_json",
        )
        # Optional: pin the exact remote node whose artifact should be pulled back.
        # Empty keeps the legacy behaviour of resolving the run's default result.
        self.result_node_id = str(properties.get("result_node_id", "") or "").strip()
        self.result_output_name = str(properties.get("result_output_name", "") or "").strip()
        self.wait_timeout_seconds = _parse_positive_int(
            properties.get("wait_timeout_seconds", DEFAULT_WAIT_TIMEOUT_SECONDS),
            name="wait_timeout_seconds",
            default=DEFAULT_WAIT_TIMEOUT_SECONDS,
        )

    def initialize(self, ctx: ProcessContext) -> None:
        workspace_root = ctx.get(RUNNER_CONTEXT_WORKSPACE_ROOT, ".piflow/workspace")
        self._workspace_root = Path(str(workspace_root)).expanduser().resolve()
        self._workspace_root.mkdir(parents=True, exist_ok=True)

    def perform(
        self,
        inputs: JobInputStream,
        outputs: JobOutputStream,
        ctx: JobContext,
    ) -> None:
        client = self._create_client()
        try:
            submit_resp = client.submit_dag(self.subdag_definition_json)
            run_id = str(submit_resp.run_id)
            self._wait_for_success(client, run_id)
            meta = client.get_run_result_meta(
                run_id=run_id,
                result_node_id=self.result_node_id,
                result_output_name=self.result_output_name,
            )
            target_path = self._prepare_output_path(ctx, meta.file_name or "remote_result.bin")
            local_path = client.download_result(
                run_id=run_id,
                result_node_id=self.result_node_id,
                result_output_name=self.result_output_name,
                target_path=target_path,
            )
        finally:
            client.close()

        outputs.write(FileArtifact(path=str(local_path)), OUTPUT_PORT)

    def _create_client(self) -> RemoteExecutionGateway:
        factory = getattr(self, "client_factory", None)
        if callable(factory):
            return factory(self)

        from piflow_engine.cn.piflow.remote.client import RemoteExecutionClient

        return RemoteExecutionClient(self.remote_grpc_target)

    def _wait_for_success(self, client: RemoteExecutionGateway, run_id: str) -> None:
        deadline = time.monotonic() + self.wait_timeout_seconds
        while True:
            status_resp = client.get_run_status(run_id)
            status = str(status_resp.status or "")
            if status == "SUCCESS":
                return
            if status in {"FAILED", "CANCELLED"}:
                raise RuntimeError(f"remote subdag failed with status {status}: {status_resp.message}")
            if time.monotonic() >= deadline:
                raise TimeoutError(
                    f"remote subdag {run_id} did not finish within "
                    f"{self.wait_timeout_seconds}s (last status={status or 'UNKNOWN'})"
                )
            time.sleep(POLL_INTERVAL_SECONDS)

    def _prepare_output_path(self, ctx: JobContext, file_name: str) -> Path:
        if self._workspace_root is None:
            raise RuntimeError("workspace root is not initialized")

        process_id = ctx.get_process_context().get_process().pid()
        stop_name = safe_name(ctx.get_stop_job().get_stop_name())
        job_id = ctx.get_stop_job().jid()
        output_dir = (
            self._workspace_root
            / process_id
            / f"{stop_name}_{job_id}_{uuid.uuid4().hex[:8]}"
            / "output"
        )
        output_dir.mkdir(parents=True, exist_ok=True)
        # NOTE: must not be named `safe_name` -- assigning that name anywhere in this
        # function would make the module-level `safe_name` function a local variable
        # for the whole scope, breaking its use above with UnboundLocalError.
        resolved_name = Path(file_name).name or "remote_result.bin"
        return output_dir / resolved_name


def _require_non_empty_string(value: Any, *, name: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{name} must not be empty")
    return text


def _parse_positive_int(value: Any, *, name: str, default: int) -> int:
    if value is None or value == "":
        return default
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be an integer") from exc
    if parsed <= 0:
        raise ValueError(f"{name} must be positive")
    return parsed


def _normalize_json(value: Any, *, name: str) -> str:
    text = _require_non_empty_string(value, name=name)
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{name} must be valid json") from exc
    return json.dumps(parsed, ensure_ascii=False)
