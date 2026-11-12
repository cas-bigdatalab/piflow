"""Automatic secrets are durable, private and shared by concurrent producers."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
from threading import Barrier, Event

import pytest

from .. import artifact_storage as storage


@pytest.fixture
def key_root(tmp_path, monkeypatch):
    root = tmp_path / "private-artifacts"
    monkeypatch.setenv("DATASET_QA_ARTIFACT_ROOT", str(root))
    monkeypatch.delenv("DATASET_QA_ARTIFACT_SIGNING_KEY", raising=False)
    return root


@pytest.mark.parametrize("value", [None, "", "  "])
def test_absent_key_is_created_once_and_reused(key_root, monkeypatch, value):
    if value is not None:
        monkeypatch.setenv("DATASET_QA_ARTIFACT_SIGNING_KEY", value)
    key = storage.signing_key()
    assert len(key) == 64 and bytes.fromhex(key)
    path = key_root / ".signing-key"
    before = path.stat()
    assert path.read_text(encoding="ascii") == key
    if os.name != "nt":
        assert stat.S_IMODE(before.st_mode) == 0o600
    assert storage.StorageConfig.load().secret == key
    assert storage.signing_key() == key and path.stat().st_mtime_ns == before.st_mtime_ns
    assert not list(key_root.glob(".signing-key-*"))
    assert key not in repr(storage.StorageConfig.load())


def test_explicit_secret_keeps_exact_value_and_does_not_touch_disk(key_root, monkeypatch):
    supplied = " existing secret with intentional whitespace "
    monkeypatch.setenv("DATASET_QA_ARTIFACT_SIGNING_KEY", supplied)
    assert storage.signing_key() == supplied
    assert not key_root.exists()
    monkeypatch.delenv("DATASET_QA_ARTIFACT_SIGNING_KEY")
    automatic = storage.signing_key()
    monkeypatch.setenv("DATASET_QA_ARTIFACT_SIGNING_KEY", supplied)
    assert storage.signing_key() == supplied
    assert (key_root / ".signing-key").read_text() == automatic
    monkeypatch.delenv("DATASET_QA_ARTIFACT_SIGNING_KEY")
    assert storage.signing_key() == automatic


def test_simultaneous_initializers_publish_only_one_complete_key(key_root, monkeypatch):
    link = storage.os.link
    barrier = Barrier(8)
    def simultaneous(source, destination):
        assert Path(source).stat().st_size == 64
        barrier.wait(timeout=10)
        return link(source, destination)
    monkeypatch.setattr(storage.os, "link", simultaneous)
    with ThreadPoolExecutor(max_workers=8) as pool:
        keys = list(pool.map(lambda _: storage.signing_key(), range(8)))
    assert len(set(keys)) == 1
    assert (key_root / ".signing-key").read_text() == keys[0]
    assert not list(key_root.glob(".signing-key-*"))


def test_separate_processes_and_restart_share_one_signing_identity(key_root):
    script = '''
import hashlib, json
from scientific_agents.dataset_qa.artifact_storage import signing_key
from scientific_agents.dataset_qa.artifacts import execution_metadata
key = signing_key()
print(json.dumps({"digest": hashlib.sha256(key.encode()).hexdigest(),
    "metadata": execution_metadata("owner", "request", {"value": 1}, 60)}))
'''
    def child():
        result = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True, timeout=30, check=True)
        return json.loads(result.stdout)
    with ThreadPoolExecutor(max_workers=4) as pool:
        outputs = list(pool.map(lambda _: child(), range(4)))
    outputs.append(child())  # A new interpreter after all initializers have exited.
    secret = storage.signing_key()
    from services.corpus_connector_service import _check_execution
    for output in outputs:
        assert output["digest"] == hashlib.sha256(secret.encode()).hexdigest()
        assert _check_execution(output["metadata"]["piflow_execution"], {"value": 1}, secret)["user"] == "owner"
    assert not list(key_root.glob(".signing-key-*"))


@pytest.mark.parametrize("content", [b"", b"partial", b"0"*65, b"x"*64, b"\xff"*64])
def test_invalid_existing_key_is_never_silently_replaced(key_root, content):
    key_root.mkdir()
    path = key_root / ".signing-key"
    path.write_bytes(content)
    path.chmod(0o600)
    with pytest.raises(storage.ArtifactStorageError) as raised:
        storage.signing_key()
    assert raised.value.phase == "configuration" and path.read_bytes() == content
    if content:
        assert content.decode("ascii", errors="replace") not in str(raised.value)
    assert not list(key_root.glob(".signing-key-*"))


def test_existing_store_without_key_requires_restoration(key_root):
    secret = storage.signing_key()
    owner = key_root / ("a"*64)
    owner.mkdir()
    (key_root / ".signing-key").unlink()
    with pytest.raises(storage.ArtifactStorageError, match="existing store"):
        storage.signing_key()
    assert not (key_root / ".signing-key").exists()
    path = key_root / ".signing-key"
    path.write_text(secret, encoding="ascii")
    path.chmod(0o600)
    assert storage.signing_key() == secret


def test_stale_incomplete_temporary_file_does_not_become_a_key(key_root):
    key_root.mkdir()
    stale = key_root / ".signing-key-interrupted"
    stale.write_bytes(b"incomplete")
    unrelated = key_root / "volume-metadata"
    unrelated.mkdir()
    key = storage.signing_key()
    assert len(key) == 64 and stale.read_bytes() == b"incomplete" and unrelated.is_dir()


@pytest.mark.parametrize("phase", ["create", "sync", "publish"])
def test_initialization_failure_is_typed_and_next_attempt_can_recover(key_root, monkeypatch, phase):
    with monkeypatch.context() as patch:
        def unavailable(*args, **kwargs):
            raise OSError("PRIVATE_INITIALIZATION_DIAGNOSTIC")
        target, name = {"create": (storage.tempfile, "mkstemp"),
                        "sync": (storage.os, "fsync"), "publish": (storage.os, "link")}[phase]
        patch.setattr(target, name, unavailable)
        with pytest.raises(storage.ArtifactStorageError) as raised:
            storage.signing_key()
        assert raised.value.phase == "configuration"
        assert "PRIVATE_INITIALIZATION_DIAGNOSTIC" not in str(raised.value)
    assert not (key_root / ".signing-key").exists()
    assert not list(key_root.glob(".signing-key-*"))
    assert len(storage.signing_key()) == 64


def test_reader_never_uses_a_key_before_publication(key_root, monkeypatch):
    link = storage.os.link
    writing, release = Event(), Event()
    def paused(source, destination):
        writing.set()
        assert release.wait(timeout=10)
        return link(source, destination)
    monkeypatch.setattr(storage.os, "link", paused)
    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(storage.signing_key)
        assert writing.wait(timeout=10)
        assert not (key_root / ".signing-key").exists()
        second = pool.submit(storage.signing_key)
        release.set()
        assert first.result(timeout=10) == second.result(timeout=10)


def test_key_path_cannot_be_a_directory_or_redirect(key_root, tmp_path):
    key_root.mkdir()
    path = key_root / ".signing-key"
    outside = tmp_path / "outside"
    outside.mkdir()
    try:
        path.symlink_to(outside, target_is_directory=True)
    except OSError:
        if sys.platform != "win32":
            raise
        import _winapi
        _winapi.CreateJunction(str(outside), str(path))
    with pytest.raises(storage.ArtifactStorageError):
        storage.signing_key()
    assert not list(outside.iterdir())


def test_posix_key_permissions_are_checked_even_for_existing_files(key_root, monkeypatch):
    storage.signing_key()
    original = storage.os.fstat
    from types import SimpleNamespace
    def readable_by_others(fd):
        value = original(fd)
        return SimpleNamespace(st_mode=value.st_mode | 0o044)
    # Exercise the POSIX permission check on every test host without changing
    # the interpreter's global os.name or Windows ACLs.
    platform = SimpleNamespace(**vars(storage.os))
    platform.name, platform.fstat = "posix", readable_by_others
    monkeypatch.setattr(storage, "os", platform)
    with pytest.raises(storage.ArtifactStorageError, match="permissions"):
        storage.signing_key()
