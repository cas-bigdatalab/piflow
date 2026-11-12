"""Local artifact storage shared by producers and callers; no agent runtime.

DATASET_QA_ARTIFACT_ROOT: private persistent directory, defaults to a sibling of workspace.
DATASET_QA_ARTIFACT_BASE_URL: externally reachable MCP HTTP base, required for local downloads.
DATASET_QA_ARTIFACT_SIGNING_KEY: stable, private key shared by QA and MCP processes.

Configuration is checked only when artifacts are used. Existing read-only tools
do not require artifact storage. Neither credentials nor paths are model inputs.
"""
from contextlib import contextmanager
from dataclasses import dataclass, field
import base64
import hashlib
import hmac
import json
import os
from pathlib import Path
import re
import shutil
import tempfile
import time
from urllib.parse import quote, urlsplit


class ArtifactStorageError(ValueError):
    """Private diagnostic; callers expose only the typed, public outcome."""


def signing_key():
    key = os.environ.get("DATASET_QA_ARTIFACT_SIGNING_KEY", "")
    if not key.strip():
        raise ArtifactStorageError("DATASET_QA_ARTIFACT_SIGNING_KEY is required")
    return key


def persistent_root():
    from infra.config_loader import PROJECT_ROOT
    from runtime.workspace_manager import WorkspaceManager
    workspace = WorkspaceManager().root.resolve()
    value = os.environ.get("DATASET_QA_ARTIFACT_ROOT", "").strip()
    root = Path(value).expanduser().resolve() if value else workspace.with_name(workspace.name+"-qa-artifacts")
    # The host exposes these trees through existing download/static routes.
    # Keep private artifacts outside them instead of changing shared routers.
    if any(root.is_relative_to(public.resolve()) for public in (workspace, PROJECT_ROOT / "storage")):
        raise ArtifactStorageError("Artifact root must be outside publicly served directories")
    return root


@dataclass(frozen=True)
class StorageConfig:
    root: Path
    secret: str = field(repr=False)
    base_url: str

    @classmethod
    def load(cls):
        return cls(persistent_root(), signing_key(),
                   os.environ.get("DATASET_QA_ARTIFACT_BASE_URL", "").strip().rstrip("/"))

    def download_base(self):
        try:
            url = urlsplit(self.base_url)
            if (url.scheme not in {"http", "https"} or not url.hostname or url.username
                    or url.password or url.query or url.fragment or url.port == 0
                    or any(c.isspace() for c in self.base_url)):
                raise ValueError()
        except ValueError as exc:
            raise ArtifactStorageError("DATASET_QA_ARTIFACT_BASE_URL must be an absolute MCP HTTP base URL") from exc
        return self.base_url


def sign_token(secret, domain, body):
    raw = json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    encoded = base64.urlsafe_b64encode(raw.encode()).decode().rstrip("=")
    signature = hmac.new(secret.encode(), (domain+"\n"+raw).encode(), "sha256").hexdigest()
    return encoded+"."+signature


def verify_token(secret, domain, token):
    try:
        encoded, signature = token.split(".")
        if not secret or not re.fullmatch(r"[A-Za-z0-9_-]{1,2000}", encoded):
            raise ValueError()
        body = json.loads(base64.urlsafe_b64decode(encoded+"="*(-len(encoded)%4)))
        if not isinstance(body, dict) or not hmac.compare_digest(sign_token(secret, domain, body), token):
            raise ValueError()
        return body
    except (ValueError, TypeError, UnicodeError, AttributeError) as exc:
        raise ValueError("需要有效的文件访问凭据") from exc


def check_identity(owner, key=None):
    if not isinstance(owner, str) or not re.fullmatch(r"[a-f0-9]{64}", owner):
        raise ValueError("无效的产物所有者")
    if key is not None and (not isinstance(key, str) or not re.fullmatch(r"[a-f0-9]{64}", key)):
        raise ValueError("无效的产物标识")


@contextmanager
def storage_operation():
    try:
        yield
    except ArtifactStorageError:
        raise
    except Exception as exc:
        raise ArtifactStorageError("Artifact storage operation could not complete") from exc


class LocalArtifactStore:
    """Immutable operation files, committed by atomically publishing a manifest."""
    def __init__(self, config, owner):
        check_identity(owner)
        self.config, self.owner = config, owner

    def path(self, key, name):
        check_identity(self.owner, key)
        if name not in {"manifest.json", "data.csv", "data.jsonl"}:
            raise ValueError("无效的产物文件名")
        path = self.config.root / self.owner / key / name
        # Reject symlink escapes, including links to another owner's directory.
        if path.resolve() != path:
            raise ArtifactStorageError("Artifact path must not follow symlinks")
        return path

    def prepare(self):
        self.config.download_base()
        with storage_operation():
            self.config.root.mkdir(parents=True, exist_ok=True, mode=0o700)

    def read_json(self, key):
        with storage_operation():
            path = self.path(key, "manifest.json")
            try:
                with path.open("rb") as source:
                    body = source.read(256 * 1024 + 1)
            except FileNotFoundError:
                return None
            if len(body) > 256 * 1024:
                raise ArtifactStorageError("Artifact manifest exceeds budget")
            value = json.loads(body)
            if not isinstance(value, dict):
                raise ArtifactStorageError("Invalid artifact manifest")
            return value

    def stat_size(self, key, fmt):
        with storage_operation():
            return self.path(key, "data."+fmt).stat().st_size

    def read_bytes(self, key, fmt, limit):
        with storage_operation():
            with self.path(key, "data."+fmt).open("rb") as source:
                return source.read(limit+1)

    @contextmanager
    def _write(self, key, name, size):
        with storage_operation():
            target = self.path(key, name)
            target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            if shutil.disk_usage(target.parent).free < size+65536:
                raise ArtifactStorageError("Insufficient artifact storage capacity")
            fd, temporary = tempfile.mkstemp(prefix=".pending-", dir=target.parent)
            try:
                with os.fdopen(fd, "wb") as output:
                    yield output
                    output.flush()
                    os.fsync(output.fileno())
                os.replace(temporary, target)
                if os.name != "nt":
                    directory = os.open(target.parent, os.O_RDONLY)
                    try:
                        os.fsync(directory)
                    finally:
                        os.close(directory)
            finally:
                Path(temporary).unlink(missing_ok=True)

    def put_file(self, key, path, fmt):
        with self._write(key, "data."+fmt, path.stat().st_size) as output, path.open("rb") as source:
            shutil.copyfileobj(source, output, length=1024 * 1024)

    def put_json(self, key, body):
        with self._write(key, "manifest.json", len(body)) as output:
            output.write(body)

    def url(self, key, resource):
        check_identity(self.owner, key)
        token = sign_token(self.config.secret, "qa-download-v1", {
            "owner": self.owner, "key": key, "expires": int(time.time())+3600})
        return self.config.download_base()+"/artifacts/"+token+"/"+quote(resource["name"], safe="")


def local_download(token, name, max_bytes):
    """Validate a short-lived download capability before opening any file."""
    config = StorageConfig.load()
    body = verify_token(config.secret, "qa-download-v1", token)
    if (set(body) != {"owner", "key", "expires"} or type(body["expires"]) is not int
            or not time.time() < body["expires"] <= time.time()+3600):
        raise ValueError("文件下载凭据已过期或无效")
    check_identity(body["owner"], body["key"])
    store = LocalArtifactStore(config, body["owner"])
    manifest = store.read_json(body["key"])
    resource = manifest.get("resource") if manifest else None
    if not resource:
        raise FileNotFoundError("结果文件暂不可用")
    if not isinstance(resource, dict):
        raise ArtifactStorageError("Invalid artifact resource metadata")
    if name != resource.get("name"):
        raise ValueError("文件下载凭据不匹配")
    with storage_operation():
        path = store.path(body["key"], "data."+resource["format"])
        if path.stat().st_size != resource["size_bytes"] or not 0 <= resource["size_bytes"] <= max_bytes:
            raise ArtifactStorageError("Artifact size differs from its committed manifest")
        digest = hashlib.sha256()
        with path.open("rb") as source:
            for chunk in iter(lambda: source.read(1024 * 1024), b""):
                digest.update(chunk)
        if digest.hexdigest() != resource["sha256"]:
            raise ArtifactStorageError("Artifact checksum differs from its committed manifest")
    return path, resource["name"], resource["format"]
