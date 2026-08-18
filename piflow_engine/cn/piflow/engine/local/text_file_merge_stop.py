from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

from piflow_engine.cn.piflow.core.artifact import FileArtifact
from piflow_engine.cn.piflow.core.runtime_context import JobContext, ProcessContext
from piflow_engine.cn.piflow.core.runtime_keys import RUN_CONTEXT_FINAL_OUTPUT_PATH
from piflow_engine.cn.piflow.core.stop import ConfigurableStop
from piflow_engine.cn.piflow.core.stream import JobInputStream, JobOutputStream
from piflow_engine.cn.piflow.engine.local.constants import RUNNER_CONTEXT_WORKSPACE_ROOT
from piflow_engine.cn.piflow.runtime.logging.path_utils import safe_name


LEFT_PORT = "left"
RIGHT_PORT = "right"
OUTPUT_PORT = "output"


class TextFileMergeStop(ConfigurableStop):
    author_email = ""
    description = "Merge two text file artifacts into one output file."
    inport_list = [LEFT_PORT, RIGHT_PORT]
    outport_list = [OUTPUT_PORT]

    def __init__(self) -> None:
        super().__init__()
        self.separator = "\n"
        self.output_file_name = "merged.txt"
        self.encoding = "utf-8"
        self._workspace_root: Path | None = None

    def set_properties(self, properties: dict[str, Any]) -> None:
        separator = properties.get("separator", "\n")
        output_file_name = properties.get("output_file_name", "merged.txt")
        encoding = properties.get("encoding", "utf-8")

        if not isinstance(separator, str):
            raise TypeError("text merge separator must be a string")
        if not isinstance(output_file_name, str):
            raise TypeError("text merge output_file_name must be a string")
        if not isinstance(encoding, str):
            raise TypeError("text merge encoding must be a string")

        self.separator = separator
        self.output_file_name = output_file_name.strip() or "merged.txt"
        self.encoding = encoding.strip() or "utf-8"

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
        left_path = self._read_input_file(inputs, LEFT_PORT)
        right_path = self._read_input_file(inputs, RIGHT_PORT)

        merged_text = (
            left_path.read_text(encoding=self.encoding)
            + self.separator
            + right_path.read_text(encoding=self.encoding)
        )

        output_path = self._prepare_output_path(ctx)
        output_path.write_text(merged_text, encoding=self.encoding)

        ctx.put(RUN_CONTEXT_FINAL_OUTPUT_PATH, str(output_path))
        outputs.write(FileArtifact(path=str(output_path)), OUTPUT_PORT)

    def _read_input_file(self, inputs: JobInputStream, port_name: str) -> Path:
        artifact = inputs.read(port_name)
        path = getattr(artifact, "path", "") or str(getattr(artifact, "value", ""))
        if not path:
            raise ValueError(f"text merge input artifact has no file path for port {port_name}")

        resolved = Path(path).expanduser().resolve()
        if not resolved.exists():
            raise FileNotFoundError(f"text merge input file not found: {resolved}")
        if not resolved.is_file():
            raise ValueError(f"text merge input path is not a file: {resolved}")
        return resolved

    def _prepare_output_path(self, ctx: JobContext) -> Path:
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
        return output_dir / (Path(self.output_file_name).name or "merged.txt")
