from __future__ import annotations

import json
from abc import ABC, abstractmethod
from pathlib import Path

from piflow_engine.cn.piflow.engine.local.spec import CommandSpec


class BundleResolver(ABC):
    @abstractmethod
    def resolve(self, bundle: str) -> CommandSpec:
        ...


class FileBundleResolver(BundleResolver):
    def __init__(self, root_dir: str | Path | None = None):
        self._root_dir = Path(root_dir).resolve() if root_dir else None

    def resolve(self, bundle: str) -> CommandSpec:
        path = Path(bundle)
        if not path.is_absolute():
            if self._root_dir is not None:
                path = self._root_dir / path
            else:
                path = Path.cwd() / path
        resolved = path.resolve()
        data = json.loads(resolved.read_text(encoding="utf-8"))
        return CommandSpec.from_dict(
            data,
            source=str(resolved),
            base_dir=resolved.parent,
        )
