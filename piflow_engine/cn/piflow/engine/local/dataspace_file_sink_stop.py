from __future__ import annotations

import shutil
import uuid
from pathlib import Path
from typing import Any

from piflow_engine.cn.piflow.core.artifact import FileArtifact
from piflow_engine.cn.piflow.core.runtime_context import JobContext, ProcessContext
from piflow_engine.cn.piflow.core.runtime_keys import RUN_CONTEXT_FINAL_OUTPUT_PATH
from piflow_engine.cn.piflow.core.stop import ConfigurableStop
from piflow_engine.cn.piflow.core.stream import DEFAULT_PORT, JobInputStream, JobOutputStream
from piflow_engine.cn.piflow.engine.local.constants import RUNNER_CONTEXT_WORKSPACE_ROOT
from piflow_engine.cn.piflow.runtime.logging.path_utils import safe_name
from services.dataspace_source_service import upload_dataspace_source_directory


class DataSpaceFileSinkStop(ConfigurableStop):
    author_email = ""
    description = "Upload a managed local directory into a Dataspace directory by datasource instance id."
    inport_list = [DEFAULT_PORT]
    outport_list = [DEFAULT_PORT]

    def __init__(self) -> None:
        super().__init__()
        self.datasource_id = ""
        self.relative_path = ""
        self.overwrite = False
        self._workspace_root: Path | None = None

    def set_properties(self, properties: dict[str, Any]) -> None:
        raw_source_id = properties.get("datasource_id", properties.get("source_id", ""))
        if not isinstance(raw_source_id, str):
            raise TypeError("dataspace file sink property 'datasource_id' must be a string")
        self.datasource_id = raw_source_id.strip()
        if not self.datasource_id:
            raise ValueError("dataspace file sink property 'datasource_id' must not be empty")

        raw_relative_path = (
            properties.get("relative_path")
            or properties.get("target_relative_path")
            or ""
        )
        if not isinstance(raw_relative_path, str):
            raise TypeError("dataspace file sink property 'relative_path' must be a string")
        self.relative_path = raw_relative_path.strip()
        if not self.relative_path:
            raise ValueError("dataspace file sink property 'relative_path' must not be empty")

        overwrite = properties.get("overwrite", False)
        if isinstance(overwrite, bool):
            self.overwrite = overwrite
        elif isinstance(overwrite, str):
            self.overwrite = overwrite.strip().lower() in {"true", "1", "yes", "y"}
        else:
            raise TypeError("dataspace file sink property 'overwrite' must be boolean-like")

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

        source_path = self._read_input_file(inputs)
        managed_dir = self._prepare_managed_dir(ctx)
        staged_path = managed_dir / Path(self.relative_path.strip().lstrip("/"))
        if staged_path.exists() and not self.overwrite:
            raise FileExistsError(f"managed sink path already exists: {staged_path}")

        staged_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, staged_path)

        upload_dataspace_source_directory(
            self.datasource_id,
            remote_relative_path=".",
            local_dir=managed_dir,
        )

        ctx.put(RUN_CONTEXT_FINAL_OUTPUT_PATH, str(staged_path))
        outputs.write(FileArtifact(path=str(staged_path)), DEFAULT_PORT)

    def _read_input_file(self, inputs: JobInputStream) -> Path:
        if inputs.contains():
            artifact = inputs.read()
        else:
            ports = inputs.ports()
            if len(ports) != 1:
                raise ValueError(
                    f"dataspace file sink requires exactly one input, got ports={ports}"
                )
            artifact = inputs.read(ports[0])

        path = getattr(artifact, "path", "") or str(getattr(artifact, "value", ""))
        if not path:
            raise ValueError("dataspace file sink input artifact has no file path")

        source_path = Path(path).expanduser().resolve()
        if not source_path.exists():
            raise FileNotFoundError(f"dataspace file sink input file not found: {source_path}")
        if not source_path.is_file():
            raise ValueError(f"dataspace file sink input path is not a file: {source_path}")
        return source_path

    def _prepare_managed_dir(self, ctx: JobContext) -> Path:
        if self._workspace_root is None:
            raise RuntimeError("workspace root is not initialized")

        process_id = ctx.get_process_context().get_process().pid()
        stop_name = safe_name(ctx.get_stop_job().get_stop_name())
        job_id = ctx.get_stop_job().jid()
        managed_dir = (
            self._workspace_root
            / process_id
            / f"{stop_name}_{job_id}_{uuid.uuid4().hex[:8]}"
            / "output"
        )
        managed_dir.mkdir(parents=True, exist_ok=True)
        return managed_dir
