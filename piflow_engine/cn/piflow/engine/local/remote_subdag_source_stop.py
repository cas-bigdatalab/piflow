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

    def submit_remote_subdag(self, dag_definition_json: str): ...

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
            submit_resp = client.submit_remote_subdag(self.subdag_definition_json)
            run_id = str(submit_resp.run_id)
            self._wait_for_success(client, run_id)
            meta = client.get_run_result_meta(
                run_id=run_id,
                result_node_id="",
                result_output_name="",
            )
            target_path = self._prepare_output_path(ctx, meta.file_name or "remote_result.bin")
            local_path = client.download_result(
                run_id=run_id,
                result_node_id="",
                result_output_name="",
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
        while True:
            status_resp = client.get_run_status(run_id)
            status = str(status_resp.status or "")
            if status == "SUCCESS":
                return
            if status in {"FAILED", "CANCELLED"}:
                raise RuntimeError(f"remote subdag failed with status {status}: {status_resp.message}")
            time.sleep(1.0)

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
        safe_name = Path(file_name).name or "remote_result.bin"
        return output_dir / safe_name


def _require_non_empty_string(value: Any, *, name: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{name} must not be empty")
    return text


def _normalize_json(value: Any, *, name: str) -> str:
    text = _require_non_empty_string(value, name=name)
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{name} must be valid json") from exc
    return json.dumps(parsed, ensure_ascii=False)
