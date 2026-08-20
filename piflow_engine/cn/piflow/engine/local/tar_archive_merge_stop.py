from __future__ import annotations

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


INPUT_PORTS = [f"data{index}" for index in range(1, 9)]
OUTPUT_PORT = "output"


class TarArchiveMergeStop(ConfigurableStop):
    author_email = ""
    description = "Merge multiple tar file artifacts into a single tar archive."
    inport_list = INPUT_PORTS
    outport_list = [OUTPUT_PORT]

    def __init__(self) -> None:
        super().__init__()
        self.output_file_name = "result.tar"
        self._workspace_root: Path | None = None

    def set_properties(self, properties: dict[str, Any]) -> None:
        output_file_name = str(properties.get("output_file_name", "result.tar")).strip()
        if not output_file_name:
            output_file_name = "result.tar"
        self.output_file_name = Path(output_file_name).name

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

        input_ports = sorted(
            (str(port) for port in inputs.ports()),
            key=_input_port_sort_key,
        )
        if len(input_ports) < 2:
            raise ValueError(
                f"tar merge requires at least two input ports, got {input_ports}"
            )
        if len(input_ports) > 8:
            raise ValueError(
                f"tar merge supports at most eight input ports, got {input_ports}"
            )

        input_files = [self._read_input_file(inputs, port) for port in input_ports]
        output_path = self._prepare_output_path(ctx)

        with tarfile.open(output_path, mode="w") as archive:
            for file_path in input_files:
                self._append_input(archive, file_path)

        ctx.put(RUN_CONTEXT_FINAL_OUTPUT_PATH, str(output_path))
        outputs.write(
            FileArtifact(path=str(output_path)).with_metadata(
                input_files=[str(path) for path in input_files],
                output_file_name=self.output_file_name,
            ),
            OUTPUT_PORT,
        )

    def _read_input_file(self, inputs: JobInputStream, port_name: str) -> Path:
        artifact = inputs.read(port_name)
        path = getattr(artifact, "path", "") or str(getattr(artifact, "value", ""))
        if not path:
            raise ValueError(f"tar merge input artifact has no file path for port {port_name}")

        resolved = Path(path).expanduser().resolve()
        if not resolved.exists():
            raise FileNotFoundError(f"tar merge input file not found: {resolved}")
        if not resolved.is_file():
            raise ValueError(f"tar merge input path is not a file: {resolved}")
        return resolved

    @staticmethod
    def _append_input(output_archive: tarfile.TarFile, input_path: Path) -> None:
        if not tarfile.is_tarfile(input_path):
            output_archive.add(input_path, arcname=input_path.name)
            return

        # Copy archive members directly into the result. Nothing is extracted
        # to the filesystem, so member paths cannot escape the workspace.
        with tarfile.open(input_path, mode="r:*") as input_archive:
            for member in input_archive.getmembers():
                member_file = input_archive.extractfile(member) if member.isfile() else None
                try:
                    output_archive.addfile(member, member_file)
                finally:
                    if member_file is not None:
                        member_file.close()

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


def _input_port_sort_key(port_name: str) -> tuple[str, int, str]:
    prefix = port_name.rstrip("0123456789")
    suffix = port_name[len(prefix):]
    return prefix, int(suffix) if suffix else 0, port_name
