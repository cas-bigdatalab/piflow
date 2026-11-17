"""Immutable application profiles; no model, transport or runtime imports."""
from dataclasses import dataclass
import re


@dataclass(frozen=True)
class ToolScope:
    server: str
    groups: tuple[str, ...] = ()
    tools: tuple[str, ...] = ()

    def __post_init__(self):
        if (not isinstance(self.server, str) or not self.server
                or not isinstance(self.groups, tuple) or not isinstance(self.tools, tuple)):
            raise ValueError("Tool scope requires a server and immutable selectors")
        if not (self.groups or self.tools) or any(not isinstance(x, str) or not x for x in (*self.groups, *self.tools)):
            raise ValueError("Tool scope requires explicit groups or tool names")

    def allows(self, server, name, group=None):
        return self.server == server and (name in self.tools or group in self.groups)


@dataclass(frozen=True)
class AgentProfile:
    agent_id: str
    label: str
    instructions: str = ""
    tool_scope: tuple[ToolScope, ...] | None = ()
    features: frozenset[str] = frozenset()
    namespace: str | None = None
    id_prefix: str | None = None
    resource_noun: str = "内容"
    max_concurrency: int = 2

    def __post_init__(self):
        for name in (self.agent_id, self.namespace or self.agent_id, self.id_prefix or self.agent_id):
            if not isinstance(name, str) or not re.fullmatch(r"[a-z][a-z0-9_]{0,31}", name):
                raise ValueError("Agent identities and storage namespaces must be stable identifiers")
        if (any(not isinstance(value, str) or not value for value in (self.label, self.resource_noun))
                or not isinstance(self.instructions, str)
                or type(self.max_concurrency) is not int or self.max_concurrency < 1):
            raise ValueError("Agent profile requires a label, resource noun and positive concurrency")
        if not isinstance(self.features, frozenset) or self.features - {"directory_lookup", "catalogue_search"}:
            raise ValueError("Unknown or mutable agent features")
        if self.tool_scope is not None and (not isinstance(self.tool_scope, tuple)
                or any(not isinstance(scope, ToolScope) for scope in self.tool_scope)):
            raise ValueError("Tool scopes must be an immutable tuple")

    @property
    def storage_namespace(self):
        return self.namespace or "agent_" + self.agent_id

    @property
    def session_prefix(self):
        return self.id_prefix or self.agent_id

    def table(self, suffix):
        return self.storage_namespace + "_" + suffix

    def allows_server(self, server):
        return self.tool_scope is None or any(scope.server == server for scope in self.tool_scope)

    def allows_tool(self, server, name, group=None):
        return self.tool_scope is None or any(scope.allows(server, name, group) for scope in self.tool_scope)

    def allows_builtin(self, name):
        return name != "resolve_resource" or "directory_lookup" in self.features


DATASET_QA_PROFILE = AgentProfile(
    agent_id="dataset_qa", label="智能取数", namespace="dataset_qa", id_prefix="qa",
    tool_scope=None, features=frozenset({"directory_lookup", "catalogue_search"}),
    resource_noun="数据集", max_concurrency=8,
)
