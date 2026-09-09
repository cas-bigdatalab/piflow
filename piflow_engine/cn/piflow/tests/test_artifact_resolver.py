from __future__ import annotations

from pathlib import Path

import pytest

from cn.piflow.core.artifact import FileArtifact, RemoteFileArtifact
from cn.piflow.core.artifact_resolver import ArtifactResolver


class _FakeRemoteClient:
    def __init__(self, source_file: Path):
        self._source_file = source_file
        self.closed = False

    def download_file(self, *, file_path: str, target_path: str | Path) -> str:
        assert file_path == str(self._source_file)
        target = Path(target_path)
        target.write_text(self._source_file.read_text(encoding="utf-8"), encoding="utf-8")
        return str(target)

    def close(self) -> None:
        self.closed = True


def test_artifact_resolver_resolves_local_file_path(tmp_path: Path) -> None:
    source = tmp_path / "input.txt"
    source.write_text("local", encoding="utf-8")

    resolved = ArtifactResolver(tmp_path).resolve_path(FileArtifact(path=str(source)))

    assert resolved == source.resolve()


def test_artifact_resolver_downloads_remote_file_into_workspace(tmp_path: Path) -> None:
    remote_source = tmp_path / "remote-source.txt"
    remote_source.write_text("remote", encoding="utf-8")
    client = _FakeRemoteClient(remote_source)

    resolver = ArtifactResolver(
        tmp_path,
        remote_client_factory=lambda target: client,
    )
    resolved = resolver.resolve_path(
        RemoteFileArtifact(path=str(remote_source), target_server="127.0.0.1:50061")
    )

    assert resolved.exists()
    assert resolved.parent == (tmp_path / "input" / "remote").resolve()
    assert resolved.read_text(encoding="utf-8") == "remote"
    assert client.closed is True


def test_artifact_resolver_requires_target_server_for_remote_file(tmp_path: Path) -> None:
    resolver = ArtifactResolver(tmp_path)

    with pytest.raises(ValueError, match="target_server"):
        resolver.resolve_path(RemoteFileArtifact(path="/tmp/remote.txt"))
