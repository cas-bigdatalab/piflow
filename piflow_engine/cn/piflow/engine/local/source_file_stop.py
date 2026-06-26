from __future__ import annotations

from pathlib import Path
from typing import Any

from piflow_engine.cn.piflow.core.artifact import FileArtifact
from piflow_engine.cn.piflow.core.runtime_context import JobContext, ProcessContext
from piflow_engine.cn.piflow.core.stop import ConfigurableStop
from piflow_engine.cn.piflow.core.stream import JobInputStream, JobOutputStream
from piflow_engine.cn.piflow.engine.local.constants import (
    RUNNER_CONTEXT_USER_ID,
    RUNNER_CONTEXT_WORKSPACE_ROOT,
)


OUTPUT_PORT = "output"


class SourceFileStop(ConfigurableStop):
    author_email = ""
    description = "Local file source stop."
    inport_list: list[str] = []
    outport_list = [OUTPUT_PORT]
    is_data_source = True

    def __init__(self) -> None:
        super().__init__()
        self.file_path = ""
        self._workspace_root: Path | None = None
        self._user_id: str | None = None

    def set_properties(self, properties: dict[str, Any]) -> None:
        raw_path = properties.get("file_path", "")
        if not isinstance(raw_path, str):
            raise TypeError("source file property 'file_path' must be a string path")
        self.file_path = raw_path

    def initialize(self, ctx: ProcessContext) -> None:
        if not self.file_path:
            raise ValueError("source file stop requires property 'file_path'")
        workspace_root = ctx.get(RUNNER_CONTEXT_WORKSPACE_ROOT, None)
        if workspace_root:
            self._workspace_root = Path(str(workspace_root)).expanduser().resolve()
        user_id = ctx.get(RUNNER_CONTEXT_USER_ID, None)
        if user_id:
            self._user_id = str(user_id).strip() or None
        path = self._resolve_source_path()
        if not path.exists():
            raise FileNotFoundError(f"source file not found: {path}")
        if not path.is_file():
            raise ValueError(f"source path is not a file: {path}")
        self.file_path = str(path)

    def perform(
        self,
        inputs: JobInputStream,
        outputs: JobOutputStream,
        ctx: JobContext,
    ) -> None:
        outputs.write(FileArtifact(path=self.file_path), OUTPUT_PORT)

    def _resolve_source_path(self) -> Path:
        raw_path = self.file_path.strip()
        if self._workspace_root is not None:
            if raw_path == "workspace" or raw_path.startswith("workspace/") or raw_path.startswith("/workspace/"):
                relative_path = raw_path.removeprefix("workspace").removeprefix("/workspace").lstrip("/")
                return (self._workspace_root / relative_path).resolve()
            if self._user_id:
                return self._resolve_user_workspace_path(raw_path)

            relative_path = raw_path.lstrip("/")
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
