from pathlib import Path
from infra.config_loader import get_settings


class WorkspaceManager:

    def __init__(self):

        settings = get_settings()

        cfg = settings.workspace

        self.root = Path(cfg.root)

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

# -----------------------------
# outputs 管理
# -----------------------------

    def list_outputs(self):

        if not self.outputs.exists():
            return []

        return [p.name for p in self.outputs.iterdir()]

    def detect_new_outputs(self, before):

        after = self.list_outputs()

        new_files = list(set(after) - set(before))

        return new_files