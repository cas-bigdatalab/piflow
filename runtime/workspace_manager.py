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

    def get_user_root(self, user_id: str) -> Path:
        normalized_user_id = self._normalize_user_id(user_id)
        return (self.root / "users" / normalized_user_id).resolve()

    def ensure_user_workspace(self, user_id: str):

        settings = get_settings()
        cfg = settings.workspace
        user_root = self.get_user_root(user_id)

        dirs = [
            user_root,
            user_root / cfg.dirs.artifacts,
            user_root / cfg.dirs.outputs,
            user_root / cfg.dirs.temp,
            user_root / cfg.dirs.logs,
        ]

        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)

    def _normalize_user_relative_path(self, user_id: str, virtual_path: str) -> str:
        normalized_user_id = self._normalize_user_id(user_id)
        raw = (virtual_path or "").strip()

        if not raw:
            raise ValueError("workspace path is empty")

        user_root = self.get_user_root(normalized_user_id).resolve()
        user_prefix = f"/users/{normalized_user_id}"
        workspace_prefixes = ("/workspace/", "workspace/")
        if raw == user_prefix:
            raise ValueError("user workspace root path is not allowed")

        input_path = Path(raw)
        if input_path.is_absolute():
            resolved = input_path.resolve()
            try:
                relative = resolved.relative_to(user_root)
            except ValueError:
                relative = None
            else:
                if not relative.parts:
                    raise ValueError("user workspace root path is not allowed")
                if any(part in ("..", "") for part in relative.parts):
                    raise ValueError("user workspace path is invalid")
                return "/".join(relative.parts)

        if raw.startswith(workspace_prefixes):
            workspace_relative = raw.removeprefix("/").removeprefix("workspace/").lstrip("/")
            if not workspace_relative:
                raise ValueError("workspace root path is not allowed")
            raw = "/" + workspace_relative
        elif raw.startswith(user_prefix + "/"):
            raw = raw[len(user_prefix):]
        elif raw.startswith("/users/"):
            parts = Path(raw.lstrip("/")).parts
            if len(parts) >= 2 and parts[1] != normalized_user_id:
                raise ValueError("path belongs to another user")
            if len(parts) >= 2 and parts[1] == normalized_user_id:
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

    def resolve_user_virtual_path(
        self,
        user_id: str,
        virtual_path: str,
        create_parent: bool = False,
    ) -> Path:
        user_root = self.get_user_root(user_id).resolve()
        relative = self._normalize_user_relative_path(user_id, virtual_path)
        resolved = (user_root / relative).resolve()

        try:
            resolved.relative_to(user_root)
        except ValueError as exc:
            raise ValueError(f"path escapes user workspace: {virtual_path}") from exc

        parts = resolved.relative_to(user_root).parts
        if not parts:
            raise ValueError("user workspace root path is not allowed")

        if create_parent:
            resolved.parent.mkdir(parents=True, exist_ok=True)

        return resolved

    def to_user_relative_path(self, user_id: str, virtual_path: str) -> str:
        relative = self._normalize_user_relative_path(user_id, virtual_path)
        return "/" + relative.replace("\\", "/")

    def to_user_virtual_path(self, user_id: str, virtual_path: str) -> str:
        relative = self._normalize_user_relative_path(user_id, virtual_path)
        normalized_user_id = self._normalize_user_id(user_id)
        normalized_relative = relative.replace("\\", "/")
        return f"/users/{normalized_user_id}/{normalized_relative}"

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
