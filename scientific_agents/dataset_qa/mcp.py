"""MCP discovery from configured servers; tool schemas are loaded on demand."""
import asyncio
from collections import OrderedDict
from contextlib import AsyncExitStack, asynccontextmanager
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
import re
import time

import yaml

from .context import encode, project
from .contracts import Limits, QAError, Server
from .results import ToolResult


def terms(text):
    words = re.findall(r"[a-z0-9_]+|[^\W\d_]+", str(text).casefold())
    result = set(words)
    for word in words:
        if any(ord(c)>127 for c in word):
            result.update(word[i:i+2] for i in range(len(word)-1))
    return result


def ranked(items, query, describe):
    query = terms(query)
    if not query:
        return list(items)
    # Generic lexical retrieval, with stable browsing fallback when metadata
    # cannot match a query. No domain names, tool names or intent rules.
    return sorted(items, key=lambda value: -len(query & terms(describe(value))))


@dataclass(frozen=True)
class Tool:
    server: str
    name: str
    description: str
    schema: dict
    annotations: dict
    meta: dict

    @property
    def alias(self):
        key = sha256((self.server+"\0"+self.name).encode()).hexdigest()[:12]
        return "mcp_"+key+"_"+re.sub(r"[^a-zA-Z0-9_]", "_", self.name)[-40:]

    @property
    def title(self):
        return str(self.annotations.get("title") or self.name)[:200]

    def definition(self):
        return {"type": "function", "function": {"name": self.alias,
            "description": self.description, "parameters": self.schema}}


class MCPGateway:
    def __init__(self, servers=None, config_path=None, client_factory=None, limits=None):
        self.servers = dict(servers or {})
        self.config_path = Path(config_path) if config_path else None
        self.client_factory, self.limits = client_factory, limits or Limits()
        self.cache = {}

    def configured_servers(self):
        servers = dict(self.servers)
        if self.config_path:
            try:
                raw = yaml.safe_load(self.config_path.read_text(encoding="utf-8"))
                if raw is None:
                    raw = {}
                if not isinstance(raw, dict):
                    raise ValueError("Expected a configuration object")
                entries = raw.get("mcpServers", raw.get("servers", {}))
                if isinstance(entries, list):
                    named = {}
                    for entry in entries:
                        if not isinstance(entry, dict) or not entry.get("name") or entry["name"] in named:
                            raise ValueError("Invalid or duplicate server name")
                        named[entry["name"]] = entry
                    entries = named
                if not isinstance(entries, dict):
                    raise ValueError("Expected a server map")
                for name, entry in entries.items():
                    if not isinstance(name, str) or not name or not isinstance(entry, dict):
                        raise ValueError("Invalid server entry")
                    if not entry.get("enabled", True):
                        servers.pop(name, None)
                        continue
                    options = {k: v for k, v in entry.items() if k not in {"name", "enabled", "description", "timeout"}}
                    if not (options.get("url") or options.get("command")):
                        raise ValueError("Missing transport target")
                    if entry.get("timeout") is not None and (not isinstance(entry["timeout"], (int, float)) or entry["timeout"]<=0):
                        raise ValueError("Invalid timeout")
                    target = options["url"] if set(options)=={"url"} else {"mcpServers": {name: options}}
                    servers[name] = Server(target, str(entry.get("description", "")), entry.get("timeout"))
            except (OSError, ValueError, KeyError, TypeError, yaml.YAMLError) as exc:
                raise QAError("invalid_mcp_config", "MCP配置无法读取或格式不正确", 503) from exc
        return servers

    @asynccontextmanager
    async def session(self):
        servers = self.configured_servers()
        for name in list(self.cache):
            if name not in servers or time.monotonic()-self.cache[name][1]>=self.limits.cache_seconds:
                self.cache.pop(name, None)
        async with AsyncExitStack() as stack:
            yield ToolSession(self, servers, stack)


class ToolSession:
    def __init__(self, gateway, servers, stack):
        self.gateway, self.servers, self.stack = gateway, servers, stack
        self.clients, self.loaded = {}, OrderedDict()
        self.limits = gateway.limits

    def list_servers(self, query="", offset=0, limit=8):
        names = ranked(self.servers, query, lambda n: n+" "+self.servers[n].description)
        page = names[offset:offset+limit]
        result = {"items": [{"name": n, "description": self.servers[n].description[:300]} for n in page]}
        if offset+len(page)<len(names):
            result["next_offset"] = offset+len(page)
        return result

    async def client(self, server):
        if server not in self.servers:
            raise QAError("server_not_found", "MCP服务未配置或未启用", 404)
        if server not in self.clients:
            spec = self.servers[server]
            factory = self.gateway.client_factory
            if factory is None:
                from fastmcp import Client
                factory = Client
            try:
                async with asyncio.timeout(self.limits.connect_timeout):
                    target = spec.target() if callable(spec.target) else spec.target
                    self.clients[server] = await self.stack.enter_async_context(factory(target, timeout=spec.timeout or self.limits.timeout))
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                raise QAError("mcp_unavailable", "所选MCP服务暂不可用", 503) from exc
        return self.clients[server]

    async def tools(self, server):
        client = await self.client(server)
        spec = self.servers[server]
        # Configuration identity is part of the cache key, so changed targets
        # and credentials never reuse another server's cached schemas.
        identity = sha256(repr(spec).encode()).hexdigest()
        cached = self.gateway.cache.get(server)
        if cached and cached[0]==identity and time.monotonic()-cached[1]<self.limits.cache_seconds:
            return cached[2]
        try:
            async with asyncio.timeout(self.limits.connect_timeout):
                values = await client.list_tools()
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            raise QAError("mcp_unavailable", "无法读取所选MCP服务的工具目录", 503) from exc
        tools = []
        for value in values:
            annotations = getattr(value, "annotations", None)
            if hasattr(annotations, "model_dump"):
                annotations = annotations.model_dump(exclude_none=True)
            tools.append(Tool(server, value.name, getattr(value, "description", "") or "",
                getattr(value, "inputSchema", None) or getattr(value, "input_schema", {}) or {},
                annotations or {}, getattr(value, "meta", None) or getattr(value, "_meta", None) or {}))
        self.gateway.cache[server] = (identity, time.monotonic(), tools)
        return tools

    async def load(self, server, query="", offset=0, limit=4):
        tools = ranked(await self.tools(server), query,
            lambda t: t.name+" "+t.description+" "+encode(t.meta))
        page = tools[offset:offset+limit]
        loaded = []
        for tool in page:
            definition = tool.definition()
            if len(encode(definition))>self.limits.schema_chars:
                loaded.append({"name": tool.name, "error": "schema_too_large"})
                continue
            self.loaded.pop(tool.alias, None)
            self.loaded[tool.alias] = tool
            while len(self.loaded)>self.limits.max_tools or len(encode(self.definitions()))>self.limits.schema_chars:
                self.loaded.popitem(last=False)
            loaded.append({"name": tool.alias, "tool": tool.name, "title": tool.title})
        result = {"items": [item for item in loaded if item.get("error") or item["name"] in self.loaded]}
        if offset+len(page)<len(tools):
            result["next_offset"] = offset+len(page)
        return result

    def definitions(self):
        return [tool.definition() for tool in self.loaded.values()]

    async def call(self, alias, arguments):
        tool = self.loaded.get(alias)
        if tool is None:
            raise QAError("tool_not_loaded", "工具未加载，请先发现并加载相应定义")
        from jsonschema import Draft202012Validator, SchemaError, ValidationError

        def check_refs(value):
            if isinstance(value, dict):
                for key, child in value.items():
                    if key in {"$ref", "$dynamicRef"} and (not isinstance(child, str) or not child.startswith("#")):
                        raise QAError("invalid_schema", "工具schema仅支持本地引用", 502)
                    check_refs(child)
            elif isinstance(value, list):
                for child in value:
                    check_refs(child)

        check_refs(tool.schema)
        try:
            Draft202012Validator.check_schema(tool.schema)
            Draft202012Validator(tool.schema).validate(arguments)
        except SchemaError as exc:
            raise QAError("invalid_schema", "MCP工具schema无效", 502) from exc
        except ValidationError as exc:
            detail = {"path": list(exc.absolute_path), "constraint": exc.validator}
            raise QAError("invalid_parameters", "参数不符合当前工具schema", detail=detail) from exc
        if len(encode(arguments))>self.limits.context_chars:
            raise QAError("invalid_parameters", "工具参数超过运行预算")
        self.loaded.move_to_end(alias)
        timeout = self.servers[tool.server].timeout or self.limits.timeout
        try:
            async with asyncio.timeout(timeout):
                result = await (await self.client(tool.server)).call_tool(tool.name, arguments,
                    timeout=timeout, raise_on_error=False)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            raise QAError("execution_unknown", "MCP调用中断，无法确认执行结果；未自动重试", 502) from exc
        if getattr(result, "is_error", getattr(result, "isError", False)):
            detail, _ = project([b.text for b in getattr(result, "content", []) if getattr(b, "type", None)=="text"], 2000)
            raise QAError("tool_failed", "MCP工具返回错误", 502, detail=detail)
        # Only protocol-level errors are interpreted here. Business envelopes,
        # status codes, resource IDs and output structures belong to the server.
        return tool, ToolResult.from_mcp(result, self.limits.result_bytes)
