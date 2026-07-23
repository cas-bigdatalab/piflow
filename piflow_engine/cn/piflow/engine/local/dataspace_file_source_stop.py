from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

from piflow_engine.cn.piflow.core.artifact import FileArtifact
from piflow_engine.cn.piflow.core.runtime_context import JobContext, ProcessContext
from piflow_engine.cn.piflow.core.stop import ConfigurableStop
from piflow_engine.cn.piflow.core.stream import DEFAULT_PORT, JobInputStream, JobOutputStream
from piflow_engine.cn.piflow.engine.local.constants import RUNNER_CONTEXT_WORKSPACE_ROOT
from services.dataspace_source_service import download_dataspace_source_file


class DataspaceFileSourceStop(ConfigurableStop):
    author_email = ""
    description = "Download a Dataspace file by datasource instance id and relative path."
    inport_list: list[str] = []
    outport_list = [DEFAULT_PORT]
    is_data_source = True

    def __init__(self) -> None:
        super().__init__()
        self.datasource_id = ""
        self.relative_path = ""
        self._workspace_root: Path | None = None

    def set_properties(self, properties: dict[str, Any]) -> None:
        raw_source_id = properties.get("datasource_id", properties.get("source_id", ""))
        if not isinstance(raw_source_id, str):
            raise TypeError("dataspace file source property 'datasource_id' must be a string")
        self.datasource_id = raw_source_id.strip()
        if not self.datasource_id:
            raise ValueError("dataspace file source property 'datasource_id' must not be empty")

        raw_relative_path = properties.get("relative_path", "")
        if not isinstance(raw_relative_path, str):
            raise TypeError("dataspace file source property 'relative_path' must be a string")
        self.relative_path = raw_relative_path.strip()
        if not self.relative_path:
            raise ValueError("dataspace file source property 'relative_path' must not be empty")

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
        if self._workspace_root is None:
            raise RuntimeError("workspace root is not initialized")

        local_path = self._prepare_output_path(ctx, self.relative_path)
        result = download_dataspace_source_file(
            self.datasource_id,
            relative_path=self.relative_path,
            target_dir=local_path.parent,
        )
        downloaded_path = Path(result["localPath"]).expanduser().resolve()
        outputs.write(FileArtifact(path=str(downloaded_path)), DEFAULT_PORT)

    def _prepare_output_path(self, ctx: JobContext, relative_path: str) -> Path:
        if self._workspace_root is None:
            raise RuntimeError("workspace root is not initialized")

        process_id = ctx.get_process_context().get_process().pid()
        stop_name = ctx.get_stop_job().get_stop_name()
        job_id = ctx.get_stop_job().jid()
        sanitized_relative = relative_path.strip().lstrip("/")
        output_dir = (
            self._workspace_root
            / process_id
            / f"{stop_name}_{job_id}_{uuid.uuid4().hex[:8]}"
            / "output"
        )
        output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir / sanitized_relative


class DataspaceDataSourceStop(DataspaceFileSourceStop):
    """Backward-compatible alias for the previous class name."""

