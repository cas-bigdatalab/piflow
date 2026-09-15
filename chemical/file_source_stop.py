"""Chemical file source stop with local and remote file support."""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

from piflow_engine.cn.piflow.core.artifact import FileArtifact
from piflow_engine.cn.piflow.core.runtime_context import JobContext, ProcessContext
from piflow_engine.cn.piflow.core.stop import ConfigurableStop
from piflow_engine.cn.piflow.core.stream import JobInputStream, JobOutputStream
from piflow_engine.cn.piflow.remote.client import RemoteExecutionClient


OUTPUT_PORT = "output"
RUNNER_CONTEXT_WORKSPACE_ROOT = "local.workspace_root"


class ChemicalFileSourceStop(ConfigurableStop):
    """Read a local file or download a file from a PiFlow remote node."""

    author_email = ""
    description = "Chemical file source supporting local and remote files."
    inport_list: list[str] = []
    outport_list = [OUTPUT_PORT]
    is_data_source = True

    def __init__(self) -> None:
        super().__init__()
        self.source_type = "local"
        self.file_path = ""
        self.remote_ip = ""
        self.remote_port = 0
        self.remote_path = ""
        self._workspace_root: Path | None = None
        self._resolved_file_path: Path | None = None

    def set_properties(self, properties: dict[str, Any]) -> None:
        self.source_type = _read_source_type(properties.get("source_type", "local"))

        self.file_path = _read_optional_string(properties, "file_path")
        self.remote_ip = _read_optional_string(properties, "remote_ip")
        self.remote_path = _read_optional_string(
            properties,
            "remote_path",
            aliases=("remote_file_path",),
        )
        self.remote_port = _read_optional_port(properties.get("remote_port", 0))

        if self.source_type == "local" and not self.file_path:
            raise ValueError("chemical file source requires property 'file_path'")

        if self.source_type == "remote":
            if not self.remote_ip:
                raise ValueError("remote chemical file source requires 'remote_ip'")
            if not self.remote_port:
                raise ValueError("remote chemical file source requires 'remote_port'")
            if not self.remote_path:
                raise ValueError("remote chemical file source requires 'remote_path'")

    def initialize(self, ctx: ProcessContext) -> None:
        workspace_root = ctx.get(RUNNER_CONTEXT_WORKSPACE_ROOT, None)
        if workspace_root:
            self._workspace_root = Path(str(workspace_root)).expanduser().resolve()

        if self.source_type == "local":
            path = self._resolve_local_path()
            if not path.exists():
                raise FileNotFoundError(f"chemical source file not found: {path}")
            if not path.is_file():
                raise ValueError(f"chemical source path is not a file: {path}")
            self._resolved_file_path = path
            return

        self._resolved_file_path = self._download_remote_file(ctx)

    def perform(
        self,
        inputs: JobInputStream,
        outputs: JobOutputStream,
        ctx: JobContext,
    ) -> None:
        if self._resolved_file_path is None:
            raise RuntimeError("chemical file source is not initialized")
        outputs.write(FileArtifact(path=str(self._resolved_file_path)), OUTPUT_PORT)

    def _resolve_local_path(self) -> Path:
        raw_path = self.file_path.strip()
        if self._workspace_root is None:
            return Path(raw_path).expanduser().resolve()

        if raw_path == "workspace" or raw_path.startswith("workspace/") or raw_path.startswith("/workspace/"):
            relative_path = raw_path.removeprefix("workspace").removeprefix("/workspace").lstrip("/")
            return (self._workspace_root / relative_path).resolve()

        return (self._workspace_root / raw_path.lstrip("/")).resolve()

    def _download_remote_file(self, ctx: ProcessContext) -> Path:
        if self._workspace_root is None:
            raise RuntimeError("workspace root is required for remote chemical files")

        process_id = str(ctx.get_process().pid())
        file_name = Path(self.remote_path).name
        if not file_name or file_name in {".", ".."}:
            raise ValueError("remote chemical file path must contain a file name")

        target_dir = self._workspace_root / process_id / "chemical_inputs"
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = target_dir / f"{uuid.uuid4().hex}_{file_name}"
        client = RemoteExecutionClient(f"{self.remote_ip}:{self.remote_port}")
        try:
            client.download_file(
                file_path=self.remote_path,
                target_path=target_path,
            )
        finally:
            client.close()
        return target_path


def _read_source_type(value: Any) -> str:
    if not isinstance(value, str):
        raise TypeError("chemical file source property 'source_type' must be a string")
    source_type = value.strip().lower()
    if source_type not in {"local", "remote"}:
        raise ValueError("chemical file source 'source_type' must be 'local' or 'remote'")
    return source_type


def _read_optional_string(
    properties: dict[str, Any],
    key: str,
    *,
    aliases: tuple[str, ...] = (),
) -> str:
    for candidate in (key, *aliases):
        if candidate not in properties:
            continue
        value = properties[candidate]
        if not isinstance(value, str):
            raise TypeError(f"chemical file source property '{key}' must be a string")
        return value.strip()
    return ""


def _read_optional_port(value: Any) -> int:
    if value in (None, ""):
        return 0
    if isinstance(value, bool) or not isinstance(value, int):
        if isinstance(value, str) and value.strip().isdigit():
            value = int(value.strip())
        else:
            raise TypeError("chemical file source property 'remote_port' must be an integer")
    if not 0 <= value <= 65535:
        raise ValueError("chemical file source property 'remote_port' must be between 1 and 65535")
    return value
