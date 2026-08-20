"""Merge multiple tar archives into one output archive."""

from __future__ import annotations

import re
import tarfile
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

OUTPUT_PORT = "output"
MAX_INPUT_PORTS = 8
INPUT_PORTS = [f"data{i}" for i in range(1, MAX_INPUT_PORTS + 1)]


class TarArchiveMergeStop(ConfigurableStop):
    """Combine the members of 2-8 tar archives without extracting them."""

    author_email = ""
    description = "Merge multiple tar archive artifacts into one tar archive."
    inport_list = list(INPUT_PORTS)
    outport_list = [OUTPUT_PORT]

    def __init__(self) -> None:
        super().__init__()
        self.output_file_name = "result.tar"
        self._workspace_root: Path | None = None

    def set_properties(self, properties: dict[str, Any]) -> None:
        raw_name = properties.get("output_file_name", "result.tar")
        if not isinstance(raw_name, str):
            raise TypeError("tar merge property 'output_file_name' must be a string")
        self.output_file_name = Path(raw_name.strip() or "result.tar").name

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
        ports = sorted(inputs.ports(), key=_natural_key)
        if len(ports) < 2:
            raise ValueError(f"tar merge stop needs at least 2 inputs, got ports={ports}")

        source_paths = [self._input_path(inputs, port) for port in ports]
        output_path = self._prepare_output_path(ctx)
        write_mode = "w:gz" if output_path.name.endswith((".tar.gz", ".tgz")) else "w"

        member_count = 0
        with tarfile.open(output_path, write_mode) as target:
            for source_path in source_paths:
                try:
                    source = tarfile.open(source_path, "r:*")
                except tarfile.TarError as exc:
                    raise ValueError(f"invalid tar archive: {source_path}") from exc
                with source:
                    for member in source:
                        fileobj = source.extractfile(member) if member.isfile() else None
                        try:
                            target.addfile(member, fileobj=fileobj)
                        finally:
                            if fileobj is not None:
                                fileobj.close()
                        member_count += 1

        ctx.put(RUN_CONTEXT_FINAL_OUTPUT_PATH, str(output_path))
        outputs.write(
            FileArtifact(
                path=str(output_path),
                metadata={
                    "source_ports": ports,
                    "source_count": len(source_paths),
                    "member_count": member_count,
                },
            ),
            OUTPUT_PORT,
        )

    @staticmethod
    def _input_path(inputs: JobInputStream, port: str) -> Path:
        artifact = inputs.read(port)
        raw_path = getattr(artifact, "path", "") or str(
            getattr(artifact, "value", "")
        )
        if not raw_path:
            raise ValueError(f"tar merge input artifact has no file path for port {port}")
        path = Path(raw_path).expanduser().resolve()
        if not path.is_file():
            raise FileNotFoundError(f"tar merge input file not found: {path}")
        return path

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
        return output_dir / self.output_file_name


def _natural_key(text: str) -> tuple[Any, ...]:
    return tuple(
        int(part) if part.isdigit() else part
        for part in re.split(r"(\d+)", text)
    )
