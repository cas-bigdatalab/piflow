from __future__ import annotations

from pathlib import Path


class WorkspacePathMapper:
    def __init__(self, workspace_root: Path, container_root: str = "/workspace") -> None:
        self.workspace_root = workspace_root.resolve()
        self.container_root = container_root.rstrip("/")

    def validate_in_workspace(self, path: Path) -> Path:
        resolved = path.resolve()
        resolved.relative_to(self.workspace_root)
        return resolved

    def to_container_path(self, path: Path) -> str:
        resolved = self.validate_in_workspace(path)
        relative = resolved.relative_to(self.workspace_root)
        return f"{self.container_root}/{relative.as_posix()}"

    def container_workdir(self, host_dir: Path) -> str:
        return self.to_container_path(host_dir)
