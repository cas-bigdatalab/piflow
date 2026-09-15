from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Callable, Protocol

from piflow_engine.cn.piflow.core.artifact import Artifact, RemoteFileArtifact


class RemoteFileDownloader(Protocol):
    def download_file(self, *, file_path: str, target_path: str | Path) -> str: ...

    def close(self) -> None: ...


class ArtifactResolver:
    def __init__(
        self,
        workspace: str | Path,
        *,
        remote_client_factory: Callable[[str], RemoteFileDownloader] | None = None,
    ) -> None:
        self._workspace = Path(workspace).expanduser().resolve()
        self._remote_client_factory = remote_client_factory or self._create_remote_client

    def resolve_path(self, artifact: Artifact) -> Path:
        path = getattr(artifact, "path", "") or str(getattr(artifact, "value", "") or "")
        if not path:
            raise ValueError("artifact has no file path")

        if isinstance(artifact, RemoteFileArtifact):
            target_server = str(artifact.target_server or "").strip()
            if not target_server:
                raise ValueError("remote file artifact missing target_server")

            target_path = self._prepare_remote_target_path(path)
            client = self._remote_client_factory(target_server)
            try:
                downloaded = client.download_file(file_path=path, target_path=target_path)
            finally:
                client.close()
            return Path(downloaded).expanduser().resolve()

        return Path(path).expanduser().resolve()

    def _prepare_remote_target_path(self, remote_path: str) -> Path:
        file_name = Path(remote_path).name or "remote_file"
        digest = hashlib.sha256(remote_path.encode("utf-8")).hexdigest()[:12]
        target_dir = self._workspace / "input" / "remote"
        target_dir.mkdir(parents=True, exist_ok=True)
        return target_dir / f"{digest}_{file_name}"

    @staticmethod
    def _create_remote_client(target_server: str) -> RemoteFileDownloader:
        from piflow_engine.cn.piflow.remote.client import RemoteExecutionClient

        return RemoteExecutionClient(target_server)
