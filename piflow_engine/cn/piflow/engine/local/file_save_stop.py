from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from piflow_engine.cn.piflow.core.artifact import FileArtifact
from piflow_engine.cn.piflow.core.runtime_context import JobContext, ProcessContext
from piflow_engine.cn.piflow.core.runtime_keys import RUN_CONTEXT_FINAL_OUTPUT_PATH
from piflow_engine.cn.piflow.core.stop import ConfigurableStop
from piflow_engine.cn.piflow.core.stream import DEFAULT_PORT, JobInputStream, JobOutputStream
from piflow_engine.cn.piflow.engine.local.constants import (
    RUNNER_CONTEXT_USER_ID,
    RUNNER_CONTEXT_WORKSPACE_ROOT,
)


class FileSaveStop(ConfigurableStop):
    author_email = ""
    description = "Save one input file to an absolute path."
    inport_list = [DEFAULT_PORT]
    outport_list = [DEFAULT_PORT]

    def __init__(self) -> None:
        super().__init__()
        self.absolute_path = ""
        self.overwrite = False
        self._workspace_root: Path | None = None
        self._user_id: str | None = None

    def set_properties(self, properties: dict[str, Any]) -> None:
        raw_path = (
            properties.get("absolute_path")
            or properties.get("path")
            or properties.get("output_path")
            or ""
        )
        if not isinstance(raw_path, str):
            raise TypeError("file save absolute_path must be a string")

        self.absolute_path = raw_path
        self.overwrite = _parse_bool(properties.get("overwrite", False))

    def initialize(self, ctx: ProcessContext) -> None:
        if not self.absolute_path:
            raise ValueError("file save absolute_path must not be empty")
        workspace_root = ctx.get(RUNNER_CONTEXT_WORKSPACE_ROOT, None)
        if workspace_root:
            self._workspace_root = Path(str(workspace_root)).expanduser().resolve()
        user_id = ctx.get(RUNNER_CONTEXT_USER_ID, None)
        if user_id:
            self._user_id = str(user_id).strip() or None
        destination = self._resolve_destination()
        if not destination.is_absolute():
            raise ValueError(f"file save path must be absolute: {self.absolute_path}")

    def perform(
        self,
        inputs: JobInputStream,
        outputs: JobOutputStream,
        ctx: JobContext,
    ) -> None:
        source_path = self._read_input_file(inputs)
        destination = self._resolve_destination()

        if destination.exists() and not self.overwrite:
            raise FileExistsError(f"target file already exists: {destination}")

        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, destination)

        ctx.put(RUN_CONTEXT_FINAL_OUTPUT_PATH, str(destination))
        saved_artifact = FileArtifact(path=str(destination))
        outputs.write(saved_artifact)

    def _read_input_file(self, inputs: JobInputStream) -> Path:
        if inputs.contains():
            artifact = inputs.read()
        else:
            ports = inputs.ports()
            if len(ports) != 1:
                raise ValueError(
                    f"file save stop requires exactly one input, got ports={ports}"
                )
            artifact = inputs.read(ports[0])

        path = getattr(artifact, "path", "") or str(getattr(artifact, "value", ""))
        if not path:
            raise ValueError("file save input artifact has no file path")

        source_path = Path(path).expanduser().resolve()
        if not source_path.exists():
            raise FileNotFoundError(f"file save input file not found: {source_path}")
        if not source_path.is_file():
            raise ValueError(f"file save input path is not a file: {source_path}")

        return source_path

    def _resolve_destination(self) -> Path:
        raw_path = self.absolute_path
        if self._workspace_root is not None:
            if raw_path == "workspace" or raw_path.startswith("workspace/") or raw_path.startswith("/workspace/"):
                relative_path = raw_path.removeprefix("workspace").removeprefix("/workspace").lstrip("/")
                return (self._workspace_root / relative_path).resolve()
            if self._user_id:
                return self._resolve_user_workspace_path(raw_path)
            if raw_path.startswith("/users/"):
                relative_path = raw_path.removeprefix("/").lstrip("/")
                return (self._workspace_root / relative_path).resolve()
        return Path(raw_path).expanduser().resolve()

    def _resolve_user_workspace_path(self, raw_path: str) -> Path:
        if self._workspace_root is None:
            raise RuntimeError("workspace root is not initialized")
        if not self._user_id:
            raise RuntimeError("user id is not initialized")

        normalized_user_id = self._normalize_user_id(self._user_id)
        user_root = (self._workspace_root / "users" / normalized_user_id).resolve()
        normalized = self._normalize_user_virtual_path(raw_path, normalized_user_id)
        return (user_root / normalized).resolve()

    @staticmethod
    def _normalize_user_id(user_id: str) -> str:
        raw = (user_id or "").strip()
        if not raw:
            raise ValueError("user_id is required")
        if raw.startswith("/") or "\\" in raw:
            raise ValueError("user_id is invalid")
        parts = Path(raw).parts
        if len(parts) != 1 or parts[0] in {"", ".", ".."}:
            raise ValueError("user_id is invalid")
        return parts[0]

    @staticmethod
    def _normalize_user_virtual_path(raw_path: str, user_id: str) -> str:
        raw = (raw_path or "").strip()
        if not raw:
            raise ValueError("workspace path is empty")

        user_prefix = f"/users/{user_id}"
        if raw == user_prefix:
            raise ValueError("user workspace root path is not allowed")
        if raw.startswith(user_prefix + "/"):
            raw = raw[len(user_prefix):]
        elif raw.startswith("/users/"):
            parts = Path(raw.lstrip("/")).parts
            if len(parts) >= 2 and parts[1] != user_id:
                raise ValueError("path belongs to another user")
            if len(parts) >= 2 and parts[1] == user_id:
                raw = "/" + "/".join(parts[2:])
            else:
                raw = raw.lstrip("/")
        elif raw.startswith("/"):
            raw = raw.lstrip("/")

        relative = raw.lstrip("/")
        if not relative:
            raise ValueError("user workspace root path is not allowed")

        parts = Path(relative).parts
        if any(part in ("..", "") for part in parts):
            raise ValueError("user workspace path is invalid")

        return "/".join(parts)


def _parse_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "1", "yes", "y"}:
            return True
        if normalized in {"false", "0", "no", "n", ""}:
            return False
    raise TypeError("overwrite must be a boolean or boolean-like string")
