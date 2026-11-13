"""Local artifact storage shared by producers and callers; no agent runtime.

DATASET_QA_ARTIFACT_ROOT: private persistent directory, defaults to a sibling of workspace.
DATASET_QA_ARTIFACT_BASE_URL: optional public MCP HTTP base override. The QA HTTP
adapter supplies the mounted download route for in-process tools; remote HTTP
tools use their own request origin/mount. Non-HTTP callers need an explicit base.
DATASET_QA_ARTIFACT_URL_MODE: legacy (default) keeps the existing app.port fallback
when the request omits its port; request preserves the external HTTP/HTTPS origin.
DATASET_QA_ARTIFACT_TRUST_PROXY_HEADERS: true accepts the nearest proxy's Forwarded
or X-Forwarded-Host/Proto/Port/Prefix. Enable only behind an ingress that overwrites
client-supplied values with the public address; otherwise headers stay ignored.
Forwarded host/proto take precedence over X-Forwarded authority headers. For a
header chain use the rightmost value, never an untrusted client-supplied prefix.
A trusted proxy origin never inherits the internal app.port. An internal MCP
address or arbitrary proxy path rewrite needs the explicit public base override.
Never infer a hostname from a bind address or client IP.
For containers, mount ARTIFACT_ROOT on private persistent storage. Every instance
serving the same download origin needs those files and the same signing key.
DATASET_QA_ARTIFACT_SIGNING_KEY: optional explicit key, shared by QA and MCP processes.
Without it, .signing-key is initialized once in the private persistent root.
Processes using automatic keys must share that root; never regenerate a lost key
for an existing store. Explicit keys retain their original value and precedence.

Configuration is checked only when artifacts are used. Existing read-only tools
do not require artifact storage. Neither credentials nor paths are model inputs.
"""
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
import base64
import hashlib
import hmac
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import stat
import tempfile
import time
from urllib.parse import quote, unquote, urlsplit
from urllib.request import parse_http_list


_download_base = ContextVar("artifact_download_base", default="")


@contextmanager
def download_base_context(base_url):
    """Transport-supplied delivery origin, isolated across tasks and worker threads."""
    token = _download_base.set(base_url or "")
    try:
        yield
    finally:
        _download_base.reset(token)


def _forwarded_value(request, name):
    """Take the nearest ingress value, with bounded parsing of quoted lists."""
    value = ",".join(request.headers.getlist(name))
    if not value:
        return None
    if len(value) > 8192 or any(ord(c) < 32 or ord(c) == 127 for c in value):
        raise ValueError("Invalid forwarding header")
    values = parse_http_list(value)
    if not values or len(values) > 32 or not values[-1].strip():
        raise ValueError("Invalid forwarding chain")
    return values[-1].strip()


def _forwarded_fields(value):
    """Parse one RFC 7239 element; reject ambiguous or incomplete pairs."""
    fields, pos = {}, 0
    pattern = re.compile(r'\s*([A-Za-z][A-Za-z0-9_-]*)\s*=\s*(?:"((?:\\.|[^"\\])*)"|([^\s;,"=]+))\s*(?:;|$)')
    while pos < len(value):
        match = pattern.match(value, pos)
        if not match or match[1].lower() in fields:
            raise ValueError("Invalid Forwarded element")
        fields[match[1].lower()] = re.sub(r"\\(.)", r"\1", match[2]) if match[2] is not None else match[3]
        pos = match.end()
    return fields


def _public_authority(value):
    authority = urlsplit("http://"+value)
    if (not authority.hostname or authority.netloc != value or authority.username or authority.password
            or authority.path or authority.query or authority.fragment or authority.port == 0
            or value.endswith(":")
            or any(c.isspace() or c in "\\/?#\"'" or ord(c) < 32 or ord(c) == 127 for c in value)):
        raise ValueError("Invalid public authority")
    if ":" not in authority.hostname and not re.fullmatch(r"[A-Za-z0-9_.-]+", authority.hostname.encode("idna").decode("ascii")):
        raise ValueError("Invalid public hostname")
    return authority


def _proxy_download_base(url, request):
    """Apply explicitly trusted transport metadata; never frontend Origin/Referer."""
    forwarded = _forwarded_value(request, "forwarded")
    fields = _forwarded_fields(forwarded) if forwarded else {}
    if fields.get("host") or fields.get("proto"):
        host, scheme, port = fields.get("host"), fields.get("proto"), None
    else:
        host = _forwarded_value(request, "x-forwarded-host")
        scheme = _forwarded_value(request, "x-forwarded-proto")
        port = _forwarded_value(request, "x-forwarded-port")
    prefix = _forwarded_value(request, "x-forwarded-prefix")
    if not any((host, scheme, port, prefix)):
        return None
    authority = _public_authority(host or url.netloc)
    if scheme is not None and scheme.lower() not in {"http", "https"}:
        raise ValueError("Invalid public scheme")
    netloc = authority.netloc
    if port is not None:
        if not re.fullmatch(r"[0-9]{1,5}", port) or not 1 <= int(port) <= 65535:
            raise ValueError("Invalid public port")
        hostname = authority.hostname
        netloc = ("["+hostname+"]" if ":" in hostname else hostname)+":"+str(int(port))
    path = url.path.rstrip("/")
    if prefix is not None:
        decoded = unquote(prefix)
        if (not prefix.startswith("/") or decoded.startswith("//")
                or any(c.isspace() or c in "\\?#" or ord(c) < 32 or ord(c) == 127 for c in decoded)
                or any(part in {".", ".."} for part in decoded.split("/"))):
            raise ValueError("Invalid public prefix")
        prefix = prefix.rstrip("/")
        if prefix and path != prefix and not path.startswith(prefix+"/"):
            path = prefix+"/"+path.lstrip("/")
    return url._replace(scheme=(scheme or url.scheme).lower(), netloc=netloc, path=path).geturl()


def request_download_base(base_url, *, request=None):
    """Complete a transport origin from deployment settings, never model input.

    Explicit public URL > opted-in proxy metadata > request URL. The default
    legacy mode retains the original missing-port fallback. Request mode uses
    standard ports, and Docker Host ports are always preserved. This resolves
    addresses only; the transport must already expose the download route.
    """
    if override := os.environ.get("DATASET_QA_ARTIFACT_BASE_URL", "").strip():
        return override.rstrip("/")
    if not base_url:
        return base_url
    try:
        url = urlsplit(str(base_url))
        # Defer invalid transport/configuration addresses to artifact validation;
        # read-only QA requests should not depend on file-serving configuration.
        port = url.port
    except ValueError:
        return str(base_url)
    if (request is not None and os.environ.get("DATASET_QA_ARTIFACT_TRUST_PROXY_HEADERS", "").strip().lower()
            in {"true", "1", "yes"}):
        try:
            forwarded = _proxy_download_base(url, request)
        except ValueError:
            forwarded = None  # Ignore a malformed bundle rather than mix origins.
        if forwarded:
            return forwarded
    mode = os.environ.get("DATASET_QA_ARTIFACT_URL_MODE", "legacy").strip().lower() or "legacy"
    if mode == "legacy" and port is None and url.hostname:
        from infra.config_loader import get_settings
        port = get_settings().app.port
        return url._replace(netloc=url.netloc+":"+str(port)).geturl()
    return str(base_url)


class ArtifactStorageError(ValueError):
    """Private diagnostic; callers expose only the typed, public outcome."""
    def __init__(self, message, *, phase="storage"):
        super().__init__(message)
        self.phase = phase


def _sync_directory(path):
    if os.name != "nt":
        directory = os.open(path, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)


def _read_signing_key(path):
    # Reject links and special files before reading; bound reads even if the
    # private file was replaced. Never include file contents in diagnostics.
    if not stat.S_ISREG(path.lstat().st_mode) or path.resolve() != path:
        raise ArtifactStorageError("Artifact signing key must be a regular private file", phase="configuration")
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0) | getattr(os, "O_BINARY", 0)
    with os.fdopen(os.open(path, flags), "rb") as source:
        info = os.fstat(source.fileno())
        if not stat.S_ISREG(info.st_mode) or (os.name != "nt" and info.st_mode & 0o077):
            raise ArtifactStorageError("Artifact signing key requires owner-only permissions", phase="configuration")
        value = source.read(65)
    if not re.fullmatch(rb"[a-f0-9]{64}", value):
        raise ArtifactStorageError("Persisted artifact signing key is invalid; restore the original key", phase="configuration")
    return value.decode("ascii")


def signing_key(root=None):
    key = os.environ.get("DATASET_QA_ARTIFACT_SIGNING_KEY", "")
    if key.strip():
        return key
    with storage_operation("configuration"):
        root = root if root is not None else persistent_root()
        root.mkdir(parents=True, exist_ok=True, mode=0o700)
        path = root / ".signing-key"
        try:
            return _read_signing_key(path)
        except FileNotFoundError:
            pass
        # A missing key in an established store may mean accidental deletion
        # or removal of an explicit secret. Rotation would invalidate receipts.
        if any(re.fullmatch(r"[a-f0-9]{64}", entry.name) for entry in root.iterdir()):
            try:
                return _read_signing_key(path)  # Another initializer may have just published it.
            except FileNotFoundError as exc:
                raise ArtifactStorageError("Artifact signing key is missing from an existing store; restore the original key", phase="configuration") from exc
        fd, temporary = tempfile.mkstemp(prefix=".signing-key-", dir=root)
        try:
            with os.fdopen(fd, "wb") as output:
                output.write(secrets.token_hex(32).encode("ascii"))
                output.flush()
                os.fsync(output.fileno())
            try:
                os.link(temporary, path)  # Atomic no-overwrite publication of the complete key.
            except FileExistsError:
                pass
            _sync_directory(root)
            return _read_signing_key(path)
        finally:
            Path(temporary).unlink(missing_ok=True)


def persistent_root():
    from infra.config_loader import PROJECT_ROOT
    from runtime.workspace_manager import WorkspaceManager
    workspace = WorkspaceManager().root.resolve()
    value = os.environ.get("DATASET_QA_ARTIFACT_ROOT", "").strip()
    root = Path(value).expanduser().resolve() if value else workspace.with_name(workspace.name+"-qa-artifacts")
    # The host exposes these trees through existing download/static routes.
    # Keep private artifacts outside them instead of changing shared routers.
    if any(root.is_relative_to(public.resolve()) for public in (workspace, PROJECT_ROOT / "storage")):
        raise ArtifactStorageError("Artifact root must be outside publicly served directories", phase="configuration")
    return root


@dataclass(frozen=True)
class StorageConfig:
    root: Path
    secret: str = field(repr=False)
    base_url: str

    @classmethod
    def load(cls):
        root = persistent_root()
        override = os.environ.get("DATASET_QA_ARTIFACT_BASE_URL", "").strip()
        mode = os.environ.get("DATASET_QA_ARTIFACT_URL_MODE", "legacy").strip().lower() or "legacy"
        if not override and mode not in {"legacy", "request"}:
            raise ArtifactStorageError("Artifact URL mode must be legacy or request", phase="configuration")
        base = override or _download_base.get()
        return cls(root, signing_key(root), base.rstrip("/"))

    def download_base(self):
        try:
            url = urlsplit(self.base_url)
            if (url.scheme not in {"http", "https"} or not url.hostname or url.username or url.password
                    or url.query or url.fragment or url.port == 0 or "\\" in self.base_url
                    or any(c.isspace() or ord(c)<32 or ord(c)==127 for c in self.base_url)):
                raise ValueError()
        except ValueError as exc:
            raise ArtifactStorageError("Artifact downloads require an absolute MCP HTTP base URL", phase="configuration") from exc
        return self.base_url


def sign_token(secret, domain, body):
    raw = json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    encoded = base64.urlsafe_b64encode(raw.encode()).decode().rstrip("=")
    signature = hmac.new(secret.encode(), (domain+"\n"+raw).encode(), "sha256").hexdigest()
    return encoded+"."+signature


def canonical_numbers(value):
    """Shared execution identity: normalize JSON numbers, never stored records.

    Booleans, strings and non-integral numbers keep their original identity.
    Both signature endpoints must use this same normalization.
    """
    if isinstance(value, dict):
        return {key: canonical_numbers(item) for key, item in value.items()}
    if isinstance(value, list):
        return [canonical_numbers(item) for item in value]
    return int(value) if isinstance(value, float) and value.is_integer() else value


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
def storage_operation(phase="storage"):
    try:
        yield
    except ArtifactStorageError:
        raise
    except Exception as exc:
        raise ArtifactStorageError("Artifact storage operation could not complete", phase=phase) from exc


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
        with storage_operation("prepare"):
            self.config.root.mkdir(parents=True, exist_ok=True, mode=0o700)
            if shutil.disk_usage(self.config.root).free < 65536:
                raise ArtifactStorageError("Insufficient artifact storage capacity", phase="prepare")
            # Validate actual writes before querying a remote source. A temporary
            # probe is private, bounded and removed even when writing fails.
            with tempfile.TemporaryFile(dir=self.config.root) as probe:
                probe.write(b"qa")
                probe.flush()
                os.fsync(probe.fileno())

    def read_json(self, key):
        with storage_operation("read"):
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
        with storage_operation("publish"):
            target = self.path(key, name)
            target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            if shutil.disk_usage(target.parent).free < size+65536:
                raise ArtifactStorageError("Insufficient artifact storage capacity", phase="publish")
            fd, temporary = tempfile.mkstemp(prefix=".pending-", dir=target.parent)
            try:
                with os.fdopen(fd, "wb") as output:
                    yield output
                    output.flush()
                    os.fsync(output.fileno())
                os.replace(temporary, target)
                _sync_directory(target.parent)
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
