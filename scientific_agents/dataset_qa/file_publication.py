"""Publish opaque files using the existing owned, signed download protocol.

Producers own their data format. This layer owns execution identity, atomic
publication and replay; it never treats arbitrary bytes as tabular records.
"""
from contextlib import contextmanager
import hashlib
import hmac
import json
import os
from pathlib import Path, PureWindowsPath
import re
import tempfile
import time

import anyio

from .artifact_storage import (ArtifactStorageError, LocalArtifactStore, StorageConfig,
    canonical_numbers, sign_token)


def _encode(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _checkpoint(deadline):
    try:
        anyio.from_thread.check_cancelled()
    except RuntimeError:
        pass
    if time.time() >= deadline:
        raise TimeoutError("文件获取已到本轮处理时限")


@contextmanager
def _lock(path, deadline):
    # OS locks release on process exit; no persistent stale-lock recovery needed.
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    if path.resolve() != path:
        raise ArtifactStorageError("File lock must not follow symlinks")
    with path.open("a+b") as handle:
        handle.seek(0, 2)
        if not handle.tell():
            handle.write(b"0")
            handle.flush()
        while True:
            _checkpoint(deadline)
            try:
                handle.seek(0)
                if os.name == "nt":
                    import msvcrt
                    msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except OSError:
                time.sleep(0.05)
        try:
            yield
        finally:
            if os.name == "nt":
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _digest_file(path, checkpoint):
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            checkpoint()
            digest.update(chunk)
    return digest.hexdigest()


def publish_file(execution, arguments, namespace, producer, *, max_bytes=64 * 1024 * 1024):
    """Run producer(path, checkpoint, max_bytes), or replay its committed file.

    The producer returns public metadata including name and format; record_count
    is optional and must only be supplied when actually measured by the producer.
    """
    config = StorageConfig.load()
    context = dict(execution or {})
    signature = context.pop("signature", "")
    expected = hmac.new(config.secret.encode(), ("qa-execution-v1\n"+_encode(context)).encode(), "sha256").hexdigest()
    digest = hashlib.sha256(_encode(canonical_numbers(arguments)).encode()).hexdigest()
    if (not isinstance(signature, str) or not hmac.compare_digest(signature, expected)
            or context.get("arguments") != digest
            or not isinstance(context.get("user"), str) or not context["user"]
            or not isinstance(context.get("request_id"), str) or not context["request_id"]
            or type(context.get("deadline")) not in (int, float)
            or not time.time() < context["deadline"] <= time.time()+600):
        raise ValueError("需要有效的调用方执行凭据")
    owner = hashlib.sha256(context["user"].encode()).hexdigest()
    key = hashlib.sha256(_encode([namespace, context["request_id"], digest]).encode()).hexdigest()
    storage = LocalArtifactStore(config, owner)
    storage.prepare()
    checkpoint = lambda: _checkpoint(context["deadline"])
    with _lock(config.root / ".file-locks" / owner / key, context["deadline"]):
        result = storage.read_json(key)
        if result is None:
            fd, temporary = tempfile.mkstemp(prefix=".pending-file-", dir=config.root)
            os.close(fd)
            path = Path(temporary)
            try:
                metadata = producer(path, checkpoint, max_bytes)
                checkpoint()
                name, fmt = metadata.get("name"), metadata.get("format")
                if (not isinstance(name, str) or not name or len(name)>240 or name in {".", ".."}
                        or Path(name).name != name or PureWindowsPath(name).name != name
                        or any(ord(c)<32 or ord(c)==127 for c in name)
                        or not isinstance(fmt, str) or not re.fullmatch(r"[a-z0-9]{1,16}", fmt)):
                    raise ValueError("文件名称或格式不符合产物约定")
                size = path.stat().st_size
                if not 0 < size <= max_bytes:
                    raise ValueError("文件为空或超过本次文件大小预算")
                resource = {"kind": "file", "name": name, "format": fmt, "size_bytes": size,
                    "sha256": _digest_file(path, checkpoint),
                    "source_ref": "file-v1."+sign_token(config.secret, "qa-file-v1", {"owner": owner, "key": key})}
                for field in ("media_type", "record_count"):
                    if field in metadata:
                        resource[field] = metadata[field]
                if "record_count" in resource and (type(resource["record_count"]) is not int or resource["record_count"] < 0):
                    raise ValueError("文件记录数量无效")
                result = {**{k: v for k, v in metadata.items() if k not in resource},
                    "status": "ready", "resource": resource}
                manifest = _encode(result).encode()
                if len(manifest) > 256 * 1024:
                    raise ValueError("文件元数据超过本次保存预算")
                storage.put_file(key, path, fmt)
                checkpoint()
                storage.put_json(key, manifest)
            finally:
                path.unlink(missing_ok=True)
        resource = result.get("resource", {})
        if (resource.get("kind") != "file" or storage.stat_size(key, resource["format"]) != resource["size_bytes"]
                or _digest_file(storage.path(key, "data."+resource["format"]), checkpoint) != resource["sha256"]):
            raise ArtifactStorageError("Saved file differs from its committed manifest")
        result["downloadUrl"] = resource["downloadUrl"] = storage.url(key, resource)
        return result
