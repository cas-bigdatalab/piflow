"""One public route set. Native FastAPI handlers keep their dependencies and lifecycle."""
import asyncio
import codecs
import json
import logging
import re
from urllib.parse import urlencode

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.routing import APIRoute
from starlette.routing import Match

from .schemas import PREFIX, Action, Adapter, ChatTurn, CreateSession, Turn, event, segment

log = logging.getLogger(__name__)


class PublicRoute(APIRoute):
    def get_route_handler(self):
        handler = super().get_route_handler()
        async def checked(request):
            try:
                return await handler(request)
            except HTTPException as exc:
                message = exc.detail.get("message", str(exc.detail)) if isinstance(exc.detail, dict) else str(exc.detail)
                return JSONResponse({"code": exc.status_code, "message": message, "result": None},
                                    status_code=exc.status_code, headers=exc.headers)
            except RequestValidationError:
                return JSONResponse({"code": 422, "message": "请求参数不符合接口约定", "result": None}, status_code=422)
            except Exception:
                log.exception("Unified API failed")
                return JSONResponse({"code": 500, "message": "服务处理失败，请检查服务日志", "result": None}, status_code=500)
        return checked


class Native:
    """Call existing route handlers in-process, never another HTTP client or business engine."""
    def __init__(self, request):
        self.request = request
        from security.auth_dependency import get_current_user
        auth = request.headers.get("authorization", "")
        if not auth.startswith("Bearer "):
            raise HTTPException(401, "请登录后继续")
        self.user = str(get_current_user(token=auth[7:])["user_id"])

    @property
    def extension(self):
        ext = getattr(self.request.app.state, "scientific_agents", None)
        if ext is None:
            raise HTTPException(503, "智能体服务尚未就绪")
        return ext

    async def response(self, method, path, body=None, query=None):
        raw = json.dumps(body or {}, ensure_ascii=False).encode()
        original = self.request
        headers = [(k, v) for k, v in original.scope["headers"] if k.lower() not in {b"content-length", b"content-type"}]
        headers += [(b"content-type", b"application/json"), (b"content-length", str(len(raw)).encode())]
        root = original.scope.get("root_path", "")
        scope = {**original.scope, "method": method, "path": root + path, "raw_path": (root + path).encode(),
                 "path_params": {}, "query_string": urlencode(query or {}).encode(), "headers": headers}
        delivered = False
        async def receive():
            nonlocal delivered
            if not delivered:
                delivered = True
                return {"type": "http.request", "body": raw, "more_body": False}
            return await original.receive()
        for route in original.app.routes:
            if not isinstance(route, APIRoute) or route.path.startswith(PREFIX):
                continue
            match, extra = route.matches(scope)
            if match == Match.FULL:
                scope.update(extra)
                try:
                    response = await route.get_route_handler()(Request(scope, receive))
                except RequestValidationError as exc:
                    raise HTTPException(422, "业务参数不符合接口约定") from exc
                if response.status_code >= 400:
                    data = json.loads(response.body)
                    detail = (data.get("problem") or {}).get("message") or data.get("detail") or data.get("message") or data.get("content")
                    raise HTTPException(response.status_code, detail or "业务请求失败")
                return response
        raise HTTPException(503, "原业务接口尚未挂载")

    async def json(self, method, path, body=None, query=None):
        response = await self.response(method, path, body, query)
        data = json.loads(response.body)
        if data.get("error") or ("code" in data and data["code"] != 200):
            raise HTTPException(409, data.get("content") or data.get("message") or "业务操作未完成")
        return data

    async def events(self, path, body):
        response = await self.response("POST", path, body)
        decoder, buffer, lines, kind = codecs.getincrementaldecoder("utf-8")(), "", [], "message"
        async def chunks():
            async for chunk in response.body_iterator:
                yield chunk
            yield None  # Flush a CR terminator/UTF-8 decoder at EOF, not an incomplete frame.
        try:
            async for chunk in chunks():
                final = chunk is None
                buffer += chunk if isinstance(chunk, str) else decoder.decode(chunk or b"", final=final)
                while match := re.search(r"\r\n|\r|\n", buffer):
                    if not final and match.group() == "\r" and match.end() == len(buffer):
                        break
                    line, buffer = buffer[:match.start()], buffer[match.end():]
                    if not line:
                        if lines:
                            value = json.loads("\n".join(lines))
                            value.setdefault("type", kind)
                            yield value
                        else:
                            yield None  # Native heartbeat, no invented progress.
                        lines, kind = [], "message"
                    elif line.startswith("data:"):
                        lines.append(line[5:].removeprefix(" "))
                    elif line.startswith("event:"):
                        kind = line[6:].strip()
        finally:
            await response.body_iterator.aclose()
            if response.background:
                await response.background()

    def file_url(self, sid, tid, fid):
        from urllib.parse import quote
        return str(self.request.base_url).rstrip("/") + PREFIX + "/sessions/" + "/".join(
            (quote(sid, safe=""), "tasks", quote(tid, safe=""), "files", quote(fid, safe="")))


def install_unified(app, adapters=None):
    from .adapters.cross_dag import CrossDagAdapter
    from .adapters.forecast import ForecastAdapter
    # Extension point: one dictionary entry per adapter; no routing branches by agent.
    registry = adapters if adapters is not None else {"cross_dag": CrossDagAdapter, "forecast": ForecastAdapter}
    paths = {getattr(r, "path", "") for r in app.routes}
    if adapters is None:
        registry = {key: cls for key, cls in registry.items() if cls.session_path in paths}
    app.state.unified_adapters = registry
    router = APIRouter(prefix=PREFIX, route_class=PublicRoute)

    def adapter(native, agent_id) -> Adapter:
        cls = registry.get(agent_id)
        if cls is None:
            raise HTTPException(422, "智能体未注册")
        return cls(native)

    def remember(native, sid, agent_id):
        store = native.extension.store
        with store._lock:
            bound = store.binding(native.user, "unified:" + sid)
            if bound and bound != agent_id:
                raise HTTPException(409, "会话绑定与智能体不一致")
            if not bound:
                store.binding(native.user, "unified:" + sid, agent_id)

    async def resolve(request, sid):
        segment(sid)
        native = Native(request)
        bound = await asyncio.to_thread(native.extension.store.binding, native.user, "unified:" + sid)
        candidates = [adapter(native, bound)] if bound else [cls(native) for cls in registry.values()]
        matches = [a for a in candidates if await asyncio.to_thread(a.owns_session, sid)]
        if not matches:
            raise HTTPException(404, "会话不存在或无权访问")
        if len(matches) != 1:
            raise HTTPException(409, "会话归属不唯一")
        chosen = matches[0]
        await asyncio.to_thread(remember, native, sid, chosen.agent_id)
        return chosen

    async def resolve_task(request, tid):
        segment(tid)
        native = Native(request)
        matches = []
        for cls in registry.values():
            a = cls(native)
            if "tasks" in a.capabilities:
                sid = await asyncio.to_thread(a.task_session, tid)
                if sid and await asyncio.to_thread(a.owns_session, sid):
                    matches.append((a, sid))
        if not matches:
            raise HTTPException(404, "任务不存在或无权访问")
        if len(matches) != 1:
            raise HTTPException(409, "任务编号归属不唯一，请使用会话内的任务接口")
        return matches[0]

    def supports(a, capability):
        if capability not in a.capabilities:
            raise HTTPException(422, "该智能体不支持此能力")

    def ok(data):
        return {"code": 200, "message": "success", "result": data}

    def stream(source, sid, rid):
        async def generate():
            done = False
            try:
                async for value in source:
                    if value is None:
                        yield ": keepalive\n\n"
                        continue
                    done = value["type"] == "done"
                    yield "data: " + json.dumps({**value, "session_id": sid, "request_id": rid}, ensure_ascii=False) + "\n\n"
            except Exception as exc:
                if not isinstance(exc, HTTPException):
                    log.exception("Unified stream failed")
                value = event("error", {"code": getattr(exc, "status_code", 500),
                    "message": str(exc.detail) if isinstance(exc, HTTPException) else "服务处理失败，请检查服务日志"})
                yield "data: " + json.dumps({**value, "session_id": sid, "request_id": rid}, ensure_ascii=False) + "\n\n"
                done = False
            finally:
                await source.aclose()
            if not done:
                yield "data: " + json.dumps({**event("done", {}), "session_id": sid, "request_id": rid}) + "\n\n"
        return StreamingResponse(generate(), media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

    @router.get("")
    async def agents(request: Request):
        Native(request)
        return ok({"items": [{"agent_id": key, "name": cls.label, "capabilities": cls.capabilities} for key, cls in registry.items()]})

    @router.post("/sessions")
    async def create(body: CreateSession, request: Request):
        native = Native(request)
        a = adapter(native, body.agent_id)
        result = await a.create_session(body)
        await asyncio.to_thread(remember, native, result["session_id"], a.agent_id)
        return ok(result)

    @router.get("/sessions")
    async def sessions(request: Request, agent_id: str = "cross_dag", pageNum: int = Query(1, ge=1), pageSize: int = Query(20, ge=1, le=100)):
        return ok(await adapter(Native(request), agent_id).list_sessions(pageNum, pageSize))

    @router.get("/sessions/{sid}")
    async def session(sid: str, request: Request, after_item_id: int = Query(0, ge=0), item_limit: int = Query(1000, ge=1, le=2000),
                      after: int | None = Query(None, ge=0), limit: int | None = Query(None, ge=1, le=2000)):
        return ok(await (await resolve(request, sid)).get_session(
            sid, after if after is not None else after_item_id, limit if limit is not None else item_limit))

    @router.delete("/sessions/{sid}")
    async def delete(sid: str, request: Request):
        a = await resolve(request, sid)
        supports(a, "delete_session")
        return ok(await a.delete_session(sid))

    @router.post("/sessions/{sid}/tasks/stream")
    @router.post("/sessions/{sid}/tasks/plan/pre-bind/stream")
    async def turn(sid: str, body: Turn, request: Request):
        a = await resolve(request, sid)
        return stream(a.stream_turn(sid, body), sid, body.request_id)

    @router.post("/sessions/{sid}/chat/stream")
    async def chat(sid: str, body: ChatTurn, request: Request):
        return await turn(sid, body, request)

    @router.get("/sessions/{sid}/tasks/{tid}")
    async def task(sid: str, tid: str, request: Request):
        a = await resolve(request, sid)
        supports(a, "tasks")
        return ok(await a.get_task(sid, segment(tid)))

    @router.post("/sessions/{sid}/tasks/{tid}/actions/stream")
    async def action(sid: str, tid: str, body: Action, request: Request):
        a = await resolve(request, sid)
        supports(a, "actions")
        return stream(a.stream_action(sid, segment(tid), body), sid, body.request_id)

    @router.get("/sessions/{sid}/tasks/{tid}/results")
    async def results(sid: str, tid: str, request: Request):
        a = await resolve(request, sid)
        supports(a, "results")
        return ok(await a.get_results(sid, segment(tid)))

    @router.get("/sessions/{sid}/tasks/{tid}/files/{fid}")
    async def file(sid: str, tid: str, fid: str, request: Request):
        a = await resolve(request, sid)
        supports(a, "files")
        return await a.download_file(sid, segment(tid), segment(fid))

    # Cross DAG path shapes remain available for every registered task adapter.
    # These are aliases into the same adapters, never another execution pipeline.
    @router.get("/tasks/{tid}")
    async def task_detail(tid: str, request: Request):
        a, sid = await resolve_task(request, tid)
        return ok(await a.detail(sid, tid))

    @router.get("/tasks/{tid}/execution/status")
    async def execution_status(tid: str, request: Request, result_node_id: str | None = None, result_output_name: str | None = None):
        a, sid = await resolve_task(request, tid)
        query = {k: v for k, v in {"result_node_id": result_node_id, "result_output_name": result_output_name}.items() if v is not None}
        return ok(await a.execution_status(sid, tid, query))

    @router.post("/tasks/{tid}/bind-and-execute/stream")
    @router.post("/tasks/{tid}/actions/stream")
    async def task_action(tid: str, body: Action, request: Request):
        a, sid = await resolve_task(request, tid)
        supports(a, "actions")
        return stream(a.stream_action(sid, tid, body), sid, body.request_id)

    @router.get("/tasks/{tid}/results")
    async def task_results(tid: str, request: Request):
        a, sid = await resolve_task(request, tid)
        supports(a, "results")
        return ok(await a.get_results(sid, tid))

    # Preserve the process URLs used by the existing Cross DAG frontend.
    # Forecast has no process_id; its files continue through the common file route.
    @router.get("/execution/{process_id}/download")
    @router.get("/execution/{process_id}/status")
    async def process_resource(process_id: str, request: Request):
        a = adapter(Native(request), "cross_dag")
        return await a.process_response(segment(process_id), request.url.path.rsplit("/", 1)[-1])

    app.include_router(router)
