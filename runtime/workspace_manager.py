from pathlib import Path

from infra.config_loader import get_settings, resolve_workspace_root


class WorkspaceManager:
    def __init__(self):

        settings = get_settings()

        cfg = settings.workspace

        self.root = resolve_workspace_root(cfg.root)

        self.artifacts = self.root / cfg.dirs.artifacts
        self.outputs = self.root / cfg.dirs.outputs
        self.temp = self.root / cfg.dirs.temp
        self.logs = self.root / cfg.dirs.logs

    def ensure_workspace(self):

        dirs = [
            self.root,
            self.artifacts,
            self.outputs,
            self.temp,
            self.logs
        ]

        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)

    def get_root(self):
        return str(self.root.resolve())

    def _resolve_workspace_path(self, virtual_path: str) -> Path:
        raw = (virtual_path or "").strip()

        if not raw:
            raise ValueError("workspace path is empty")

        root_resolved = self.root.resolve()
        input_path = Path(raw)

        # Backward compatible virtual paths like /temp/a.csv should still map to
        # the workspace root. Only absolute paths already under the workspace
        # root are treated as real filesystem absolute paths.
        if raw.startswith("/"):
            if input_path.is_absolute() and str(input_path.resolve()).startswith(str(root_resolved)):
                candidate = input_path
            else:
                candidate = self.root / raw.lstrip("/")
        elif input_path.is_absolute():
            candidate = input_path
        else:
            relative = raw.lstrip("/")
            candidate = self.root / relative

        return candidate.resolve()

    def resolve_virtual_path(self, virtual_path: str, create_parent: bool = False) -> Path:

        root_resolved = self.root.resolve()
        resolved = self._resolve_workspace_path(virtual_path)

        try:
            resolved.relative_to(root_resolved)
        except ValueError as exc:
            raise ValueError(f"path escapes workspace: {virtual_path}") from exc

        parts = resolved.relative_to(root_resolved).parts
        if not parts:
            raise ValueError("workspace root path is not allowed")

        if create_parent:
            resolved.parent.mkdir(parents=True, exist_ok=True)

        return resolved

    def to_workspace_relative_path(self, virtual_path: str) -> str:

        root_resolved = self.root.resolve()
        resolved = self._resolve_workspace_path(virtual_path)

        try:
            relative = resolved.relative_to(root_resolved)
        except ValueError as exc:
            raise ValueError(f"path escapes workspace: {virtual_path}") from exc

        if not relative.parts:
            raise ValueError("workspace root path is not allowed")

        return str(relative).replace("\\", "/")

# -----------------------------
# outputs 管理
# -----------------------------

    def list_outputs(self):

        if not self.outputs.exists():
            return []

        return [p.name for p in self.outputs.iterdir()]

    def snapshot_downloadables(self) -> dict[str, tuple[int, int]]:

        snapshot: dict[str, tuple[int, int]] = {}

        for prefix, directory in (
            ("outputs", self.outputs),
            ("artifacts", self.artifacts),
        ):
            if not directory.exists():
                continue

            for path in directory.iterdir():
                if not path.is_file():
                    continue
                stat = path.stat()
                snapshot[f"/{prefix}/{path.name}"] = (stat.st_mtime_ns, stat.st_size)

        return snapshot

    def detect_new_outputs(self, before):

        after = self.list_outputs()

        new_files = list(set(after) - set(before))

        return new_files

    def detect_changed_downloadables(
        self,
        before: dict[str, tuple[int, int]] | None,
    ) -> list[str]:

        before = before or {}
        after = self.snapshot_downloadables()
        changed: list[str] = []

        for virtual_path, state in after.items():
            if before.get(virtual_path) != state:
                changed.append(virtual_path)

        changed.sort()
        return changed
