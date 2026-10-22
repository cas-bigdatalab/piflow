"""MCP discovery from configured servers; tool schemas are loaded on demand."""
import asyncio
from collections import Counter, OrderedDict
from contextlib import AsyncExitStack, asynccontextmanager
from copy import deepcopy
from dataclasses import dataclass, field, replace
from hashlib import sha256
import logging
from pathlib import Path
import re
import time

import httpx
import yaml
from anyio import BrokenResourceError, ClosedResourceError, EndOfStream

from .context import encode, project
from .contracts import Limits, QAError, Server
from .results import ToolResult

log = logging.getLogger("flow.dataset_qa.mcp")


def transient(error, depth=0):
    """Recognize transport faults by type/status, never by business error text."""
    if depth>5:
        return False
    if isinstance(error, httpx.HTTPStatusError):
        return error.response.status_code in {429, 502, 503, 504}
    if isinstance(error, (TimeoutError, ConnectionError, httpx.TimeoutException,
            httpx.NetworkError, httpx.RemoteProtocolError, BrokenResourceError, ClosedResourceError, EndOfStream)):
        return True
    if isinstance(error, BaseExceptionGroup):
        return bool(error.exceptions) and all(transient(child, depth+1) for child in error.exceptions)
    cause = error.__cause__ or error.__context__
    return cause is not None and transient(cause, depth+1)


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
    _definition: dict | None = field(default=None, repr=False, compare=False)

    @property
    def alias(self):
        key = sha256((self.server+"\0"+self.name).encode()).hexdigest()[:12]
        return "mcp_"+key+"_"+re.sub(r"[^a-zA-Z0-9_]", "_", self.name)[-40:]

    @property
    def title(self):
        return str(self.annotations.get("title") or self.name)[:200]

    def definition(self):
        if self._definition is not None:
            return deepcopy(self._definition)
        from .capabilities import definition
        return definition(self)


def check_refs(value):
    if isinstance(value, dict):
        for key, child in value.items():
            if key in {"$ref", "$dynamicRef"} and (not isinstance(child, str) or not child.startswith("#")):
                raise QAError("invalid_schema", "工具schema仅支持本地引用", 502)
            check_refs(child)
    elif isinstance(value, list):
        for child in value:
            check_refs(child)


def check_schema(schema):
    """Resolve local references without retrieving any external resource."""
    from jsonschema import Draft202012Validator, SchemaError
    from referencing import Registry, Resource
    from referencing.exceptions import Unresolvable
    from referencing.jsonschema import DRAFT202012

    try:
        Draft202012Validator.check_schema(schema)
        check_refs(schema)
        resource = Resource(schema, DRAFT202012)
        resolver = Registry().with_resource("", resource).crawl().resolver()

        def visit(current, scope):
            scope = scope.in_subresource(current)
            if isinstance(current.contents, dict):
                for key in ("$ref", "$dynamicRef"):
                    if key in current.contents:
                        scope.lookup(current.contents[key])
            for child in current.subresources():
                visit(child, scope)

        visit(resource, resolver)
    except SchemaError as exc:
        raise QAError("invalid_schema", "MCP工具schema无效", 502) from exc
    except Unresolvable as exc:
        raise QAError("invalid_schema", "MCP工具schema的本地引用目标不存在", 502) from exc


def checked_tool(tool):
    """Compile a detached definition before it can enter the callable catalogue."""
    from .capabilities import definition, profile

    tool = deepcopy(tool)
    if not isinstance(tool.name, str) or not tool.name or any(not isinstance(value, dict)
            for value in (tool.schema, tool.annotations, tool.meta)):
        raise QAError("invalid_schema", "MCP工具定义格式无效", 502)
    try:
        check_schema(tool.schema)
        descriptor = profile(tool)  # Also validate tools that need no facade.
        paths = [descriptor.collection, descriptor.object,
            *(path for sources in descriptor.bind.values() for path in sources)]
        if any(path is not None and ((path and not path.startswith("/")) or re.search(r"~(?![01])", path)) for path in paths):
            raise QAError("invalid_schema", "服务的对象来源路径须为有效JSON Pointer", 502)
        compiled = definition(tool)
        check_schema(compiled["function"]["parameters"])
        encode({"definition": compiled, "annotations": tool.annotations, "meta": tool.meta})
    except (TypeError, ValueError) as exc:
        raise QAError("invalid_schema", "MCP工具定义须为有效JSON数据", 502) from exc
    return replace(tool, _definition=compiled)


class MCPGateway:
    def __init__(self, servers=None, config_path=None, client_factory=None, limits=None):
        self.servers = dict(servers or {})
        self.config_path = Path(config_path) if config_path else None
        self.client_factory, self.limits = client_factory, limits or Limits()
        self.cache = {}
        self.identities, self.refresh_versions, self.refresh_sequence = {}, {}, 0

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
        self.identities = {name: sha256(repr(spec).encode()).hexdigest() for name, spec in servers.items()}
        for name in list(self.cache):
            if (self.identities.get(name)!=self.cache[name][0]
                    or time.monotonic()-self.cache[name][1]>=self.limits.cache_seconds):
                self.cache.pop(name, None)
        for name in self.refresh_versions.keys()-servers.keys():
            self.refresh_versions.pop(name, None)
        async with AsyncExitStack() as stack:
            yield ToolSession(self, servers, stack)


class ToolSession:
    def __init__(self, gateway, servers, stack):
        self.gateway, self.servers, self.stack = gateway, servers, stack
        self.clients, self.connections, self.loaded = {}, {}, OrderedDict()
        self.connection_errors, self.discovery_errors = {}, {}
        self.definition_errors = {}
        self.limits = gateway.limits

    async def retry(self, error, attempt, deadline, server, phase):
        if (attempt>=self.limits.transport_retries or not transient(error)
                or asyncio.get_running_loop().time()+self.limits.retry_delay>=deadline):
            return False
        log.info("MCP transport retry: server=%s phase=%s attempt=%s error=%s",
            server, phase, attempt+1, type(error).__name__)
        await asyncio.sleep(self.limits.retry_delay)
        return True

    async def disconnect(self, server):
        self.clients.pop(server, None)
        connection = self.connections.pop(server, None)
        if connection:
            await connection.aclose()

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
        if server in self.connection_errors:
            raise self.connection_errors[server]
        if server not in self.clients:
            spec = self.servers[server]
            factory = self.gateway.client_factory
            if factory is None:
                from fastmcp import Client
                factory = Client
            deadline = asyncio.get_running_loop().time()+self.limits.connect_timeout
            for attempt in range(self.limits.transport_retries+1):
                connection = AsyncExitStack()
                try:
                    async with asyncio.timeout_at(deadline):
                        target = spec.target() if callable(spec.target) else spec.target
                        client = await connection.enter_async_context(factory(target, timeout=spec.timeout or self.limits.timeout))
                    self.connections[server] = await self.stack.enter_async_context(connection)
                    self.clients[server] = client
                    break
                except asyncio.CancelledError:
                    await connection.aclose()
                    raise
                except Exception as exc:
                    await connection.aclose()
                    if not await self.retry(exc, attempt, deadline, server, "connect"):
                        error = QAError("mcp_unavailable", "无法连接所选MCP服务，当前操作未执行", 503)
                        self.connection_errors[server] = error
                        log.warning("MCP connection failed: server=%s error=%s", server, type(exc).__name__, exc_info=True)
                        raise error from exc
        return self.clients[server]

    def cached_tools(self, server):
        spec = self.servers[server]
        # Configuration identity is part of the cache key, so changed targets
        # and credentials never reuse another server's cached schemas.
        identity = sha256(repr(spec).encode()).hexdigest()
        cached = self.gateway.cache.get(server)
        if cached and cached[0]==identity and time.monotonic()-cached[1]<self.limits.cache_seconds:
            self.definition_errors[server] = deepcopy(cached[3])
            return deepcopy(cached[2])
        return None

    async def tools(self, server):
        if server not in self.servers:
            raise QAError("server_not_found", "MCP服务未配置或未启用", 404)
        cached = self.cached_tools(server)
        if cached is not None:
            if not cached and self.definition_errors.get(server):
                error = QAError("invalid_schema", "所选服务暂无有效工具定义", 502,
                    detail={"tools": self.definition_errors[server][:3]})
                self.discovery_errors[server] = error
                raise error
            return cached
        if server in self.discovery_errors:
            raise self.discovery_errors[server]
        started = time.monotonic()
        self.gateway.refresh_sequence += 1
        sequence = self.gateway.refresh_sequence
        self.gateway.refresh_versions[server] = sequence
        try:
            client = await self.client(server)
            async with asyncio.timeout(self.limits.connect_timeout):
                values = await client.list_tools()
        except asyncio.CancelledError:
            raise
        except QAError as exc:
            self.discovery_errors[server] = exc
            raise
        except Exception as exc:
            error = QAError("mcp_unavailable", "无法读取所选MCP服务的工具目录", 503)
            self.discovery_errors[server] = error
            log.warning("MCP discovery failed: server=%s elapsed=%.3fs error=%s",
                server, time.monotonic()-started, type(exc).__name__, exc_info=True)
            raise error from exc
        tools, errors = [], []
        duplicates = {name for name, count in Counter(getattr(value, "name", None)
            for value in values if isinstance(getattr(value, "name", None), str)).items() if count>1}
        for value in values:
            name = getattr(value, "name", None)
            try:
                if isinstance(name, str) and name in duplicates:
                    raise QAError("invalid_schema", "同一服务存在重名工具，无法确定调用目标", 502)
                annotations = getattr(value, "annotations", None)
                if hasattr(annotations, "model_dump"):
                    annotations = annotations.model_dump(exclude_none=True)
                schema = getattr(value, "inputSchema", None)
                if schema is None:
                    schema = getattr(value, "input_schema", {})
                tools.append(checked_tool(Tool(server, name, str(getattr(value, "description", "") or ""),
                    schema, annotations if annotations is not None else {},
                    getattr(value, "meta", None) or getattr(value, "_meta", None) or {})))
            except QAError as exc:
                error = {"name": str(name or "<unnamed>")[:200], "error": exc.code, "message": str(exc)[:240]}
                if error not in errors:
                    errors.append(error)
                    log.warning("MCP definition rejected: server=%s tool=%s code=%s message=%s",
                        server, error["name"], exc.code, error["message"])
        identity = sha256(repr(self.servers[server]).encode()).hexdigest()
        if self.gateway.identities.get(server)==identity and self.gateway.refresh_versions.get(server)==sequence:
            self.gateway.cache[server] = (identity, time.monotonic(), deepcopy(tools), deepcopy(errors))
        self.definition_errors[server] = errors
        log.info("MCP discovery: server=%s tools=%s elapsed=%.3fs", server, len(tools), time.monotonic()-started)
        if not tools and errors:
            error = QAError("invalid_schema", "所选服务暂无有效工具定义", 502, detail={"tools": errors[:3]})
            self.discovery_errors[server] = error
            raise error
        return tools

    def include(self, page):
        loaded = []
        for tool in page:
            if tool._definition is None:
                try:
                    tool = checked_tool(tool)
                except QAError as exc:
                    loaded.append({"name": tool.name, "error": exc.code, "message": str(exc)[:240]})
                    continue
            definition = tool.definition()
            if len(encode(definition))>self.limits.schema_chars:
                loaded.append({"name": tool.name, "error": "schema_too_large"})
                continue
            self.loaded.pop(tool.alias, None)
            self.loaded[tool.alias] = tool
            while len(self.loaded)>self.limits.max_tools or len(encode(self.definitions()))>self.limits.schema_chars:
                self.loaded.popitem(last=False)
            loaded.append({"name": tool.alias, "tool": tool.name, "title": tool.title})
        return {"items": [item for item in loaded if item.get("error") or item["name"] in self.loaded]}

    def prime(self, query, references=()):
        # Reuse descriptions and schemas, never another turn's execution results.
        candidates = [tool for server in self.servers for tool in self.cached_tools(server) or []]
        recent = {(ref.get("server"), ref.get("name")) for ref in references if isinstance(ref, dict)}
        candidates = ranked(candidates, query, lambda t: t.name+" "+t.description+" "+encode(t.meta))
        candidates.sort(key=lambda t: (t.server, t.name) not in recent)
        return self.include(candidates[:min(4, self.limits.max_tools)])

    async def load(self, server, query="", offset=0, limit=4):
        catalogue = [*await self.tools(server), *self.definition_errors.get(server, [])]
        catalogue = ranked(catalogue, query, lambda item: item.name+" "+item.description+" "+encode(item.meta)
            if isinstance(item, Tool) else item["name"])
        page = catalogue[offset:offset+limit]
        result = self.include(item for item in page if isinstance(item, Tool))
        result["items"].extend(deepcopy(item) for item in page if isinstance(item, dict))
        if offset+len(page)<len(catalogue):
            result["next_offset"] = offset+len(page)
        return result

    def definitions(self):
        return [tool.definition() for tool in self.loaded.values()]

    def validate(self, alias, arguments):
        """Validate before any execution state is committed; dispatch checks again."""
        tool = self.loaded.get(alias)
        if tool is None:
            raise QAError("tool_not_loaded", "工具未加载，请先发现并加载相应定义")
        from jsonschema import Draft202012Validator, ValidationError

        check_schema(tool.schema)
        try:
            Draft202012Validator(tool.schema).validate(arguments)
        except ValidationError as exc:
            detail = {"path": list(exc.absolute_path), "constraint": exc.validator}
            detail["expected"], _ = project(exc.validator_value, 300)
            raise QAError("invalid_parameters", "参数不符合当前工具schema", detail=detail) from exc
        if len(encode(arguments))>self.limits.context_chars:
            raise QAError("invalid_parameters", "工具参数超过运行预算")
        return tool

    async def call(self, alias, arguments):
        tool = self.validate(alias, arguments)
        self.loaded.move_to_end(alias)
        timeout = self.servers[tool.server].timeout or self.limits.timeout
        deadline = asyncio.get_running_loop().time()+timeout
        dispatched = False
        try:
            async with asyncio.timeout_at(deadline):
                client = await self.client(tool.server)
                for attempt in range(self.limits.transport_retries+1):
                    try:
                        dispatched = True
                        result = await client.call_tool(tool.name, arguments,
                            timeout=max(0.001, deadline-asyncio.get_running_loop().time()), raise_on_error=False)
                        break
                    except asyncio.CancelledError:
                        raise
                    except Exception as exc:
                        if not (tool.annotations.get("readOnlyHint") is True
                                and tool.annotations.get("idempotentHint") is True
                                and await self.retry(exc, attempt, deadline, tool.server, "call")):
                            raise
                        await self.disconnect(tool.server)
                        client = await self.client(tool.server)
        except asyncio.CancelledError:
            raise
        except QAError as exc:
            if not dispatched:
                raise
            raise QAError("execution_unknown", "MCP调用中断，无法确认执行结果；未继续重试", 502) from exc
        except Exception as exc:
            if not dispatched:
                raise QAError("mcp_unavailable", "无法连接所选MCP服务，当前操作未执行", 503) from exc
            raise QAError("execution_unknown", "MCP调用中断，无法确认执行结果；未继续重试", 502) from exc
        if getattr(result, "is_error", getattr(result, "isError", False)):
            detail, _ = project([b.text for b in getattr(result, "content", []) if getattr(b, "type", None)=="text"], 2000)
            raise QAError("tool_failed", "MCP工具返回错误", 502, detail=detail)
        # Only protocol-level errors are interpreted here. Business envelopes,
        # status codes, resource IDs and output structures belong to the server.
        return tool, ToolResult.from_mcp(result, self.limits.result_bytes)
