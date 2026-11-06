"""Declarative directory capabilities and immutable resource identities."""
from dataclasses import dataclass
from hashlib import sha256
import json

from pydantic import BaseModel, ConfigDict, Field

from ..contracts import QAError
from ..references import at_path


def digest(value):
    return sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def source_identity(server):
    target = server.target
    if callable(target):
        # Fingerprinting must never instantiate/start a transport or service.
        target = {"factory": target.__module__+"."+target.__qualname__}
    if not isinstance(target, (str, dict, list)):
        target = {"type": type(target).__module__+"."+type(target).__qualname__,
                  "name": getattr(target, "name", None), "version": getattr(target, "version", None)}
    return digest(target)


@dataclass(frozen=True)
class IndexPolicy:
    workers: int = 2
    freshness: float = 7 * 24 * 3600
    request_timeout: float = 30
    lease_seconds: float = 90
    # Content requests wait internally for their prerequisite; the enclosing
    # QA turn deadline/cancellation remains authoritative.
    lookup_wait: float = 120
    poll_seconds: float = 1
    max_nodes: int = 100_000
    max_depth: int = 100
    retries: int = 1
    refresh_backoff: float = 3600

    def __post_init__(self):
        if (self.workers<1 or self.freshness<=0 or self.request_timeout<=0 or self.lease_seconds<=0
                or self.lookup_wait<0 or self.poll_seconds<=0 or self.max_nodes<1 or self.max_depth<1 or self.retries<0
                or self.refresh_backoff<=0):
            raise ValueError("Invalid directory index budget")


class DirectorySpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    identity: list[str] = Field(min_length=1)
    parent: str
    nodes: list[str] = Field(min_length=1,
        description="Alternative JSON Pointers to a complete list of this directory's immediate children. Paged/truncated lists require an upstream aggregation adapter before indexing.")
    node_id: str
    name: str
    is_file: str
    download_url: str | None = None
    status: list[str] = Field(default_factory=list)
    success: list[str | int] = Field(default_factory=lambda: [200])

    def base(self, arguments):
        if any(arguments.get(key) in (None, "") for key in self.identity):
            raise QAError("invalid_parameters", "目录索引缺少完整的数据集身份")
        return {key: value for key, value in arguments.items() if key!=self.parent}

    def rows(self, data):
        for path in self.status:
            try:
                value = at_path(data, path)
            except QAError:
                continue
            if str(value) not in {str(code) for code in self.success}:
                raise QAError("tool_failed", "目录查询未提供可确认的结果")
        matches = []
        for path in self.nodes:
            try:
                rows = at_path(data, path)
            except QAError:
                continue
            if isinstance(rows, list):
                matches.append((path, rows))
        if len(matches)!=1:
            raise QAError("invalid_schema", "目录结果不符合已声明的节点列表结构")
        path, rows = matches[0]
        result = []
        for index, row in enumerate(rows):
            if not isinstance(row, dict):
                raise QAError("invalid_schema", "目录节点必须是对象")
            identity, name, is_file = (at_path(row, pointer) for pointer in (self.node_id, self.name, self.is_file))
            if (isinstance(identity, bool) or not isinstance(identity, (str, int)) or identity==""
                    or not isinstance(name, str) or not name or not isinstance(is_file, bool)):
                raise QAError("invalid_schema", "目录节点缺少稳定身份、名称或类型")
            url = None
            if self.download_url:
                try:
                    url = at_path(row, self.download_url)
                except QAError:
                    pass
            result.append({"key": digest(identity), "identity": identity, "name": name,
                           "kind": "file" if is_file else "directory", "url": url,
                           "raw": row, "pointer": path+"/"+str(index)})
        return result
