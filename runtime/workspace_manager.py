from pathlib import Path

from infra.config_loader import get_settings, resolve_workspace_root


class WorkspaceManager:

    ALLOWED_DIRS = {"artifacts", "outputs", "temp", "logs"}

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

    def resolve_virtual_path(self, virtual_path: str, create_parent: bool = False) -> Path:

        raw = (virtual_path or "").strip()

        if not raw:
            raise ValueError("workspace path is empty")

        input_path = Path(raw)
        if input_path.is_absolute():
            candidate = input_path
        else:
            relative = raw.lstrip("/")
            candidate = self.root / relative

        resolved = candidate.resolve()
        root_resolved = self.root.resolve()

        try:
            resolved.relative_to(root_resolved)
        except ValueError as exc:
            raise ValueError(f"path escapes workspace: {virtual_path}") from exc

        parts = resolved.relative_to(root_resolved).parts
        if not parts:
            raise ValueError("workspace root path is not allowed")

        if parts[0] not in self.ALLOWED_DIRS:
            raise ValueError(
                f"top-level workspace dir must be one of: {sorted(self.ALLOWED_DIRS)}"
            )

        if create_parent:
            resolved.parent.mkdir(parents=True, exist_ok=True)

        return resolved

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
