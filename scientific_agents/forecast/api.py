"""Dedicated forecast routes, with an optional standalone development harness."""
from contextlib import ExitStack, asynccontextmanager
from hashlib import sha256
import asyncio
import hmac
import json
import os
import secrets
import time

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from filelock import FileLock
from starlette.requests import Request as StarletteRequest

from . import bootstrap  # noqa: F401 - configure before importing the PiFlow runtime
from .config import load_settings
from .dialogue import create_interpreter
from ..gateway import AgentDirectory
from .model import create_predictor
from .persistence import Store, open_checkpointer, session_key
from .providers import Registry
from .catalog import DataCatalog, ProviderFactories
from .runtime import ForecastAgent, request_turn_id
from .schema import SessionCreateRequest, TurnInput
from .workflow import ForecastWorkflow
from .feedback import ForecastError, http_error, present, task_view

PREFIX = "/api/piflow/v1"
LABELS = {"data": "正在获取数据并检查输入质量", "predict": "正在运行固定预测模型", "assess": "正在检查预警条件和判定依据",
          "evaluate": "正在计算统计量和回测指标", "report": "正在生成图表与报告"}


def encode_sse(event):
    return "event: " + event["type"] + "\ndata: " + json.dumps(event, ensure_ascii=False, allow_nan=False) + "\n\n"


def create_app(*, legacy=None, settings=None, interpreter=None, predictor=None, providers=None, provider_factories=None, agents=(), host_resources=None, manage_legacy=True):
    cfg = settings or load_settings()

    @asynccontextmanager
    async def lifespan(app):
        resources = host_resources() if callable(host_resources) else host_resources
        if resources is not None:
            cfg.root = resources.root
        cfg.root.mkdir(parents=True, exist_ok=True)
        with ExitStack() as stack:
            stack.enter_context(FileLock(str(cfg.root / "service.lock"), timeout=0))
            # Explicit DSN is needed for production; SQLite is a durable standalone default.
            pg_dsn = resources.postgres_dsn if resources else os.getenv("FORECAST_POSTGRES_DSN")
            url = resources.database_url if resources else os.getenv("FORECAST_DATABASE_URL")
            if pg_dsn and not url:
                url = pg_dsn.replace("postgresql://", "postgresql+psycopg://", 1)
            store = Store(url or f"sqlite:///{(cfg.root / 'tasks.sqlite').as_posix()}")
            stack.callback(store.close)
            checkpointer = open_checkpointer(stack, cfg.root, pg_dsn)
            dialogue = interpreter or create_interpreter()
            model = predictor or create_predictor(cfg)
            if os.getenv("FORECAST_WARMUP", "1") == "1" and hasattr(model, "warmup"):
                await asyncio.to_thread(model.warmup)
            registry = Registry(cfg, providers) if providers is not None else (provider_factories or ProviderFactories()).build(cfg)
            await asyncio.to_thread(registry.refresh)
            agent = ForecastAgent(ForecastWorkflow(cfg, registry, model), store,
                                  checkpointer, dialogue)
            directory = AgentDirectory()
            directory.register(agent)
            for extra_agent in agents:
                directory.register(extra_agent)
            stack.callback(directory.close)
            secret_file = cfg.root / "artifact-secret"
            if not secret_file.exists():
                secret_file.write_text(secrets.token_hex(32), encoding="ascii")
            app.state.secret = secret_file.read_text(encoding="ascii")
            app.state.agents, app.state.store, app.state.forecast = directory, store, agent
            sessions = None
            if host_resources is not None:
                from .sessions import HostSessions
                sessions = HostSessions(agent)
                agent.session_manager = sessions
            app.state.sessions = sessions

            stopping = asyncio.Event()

            async def reconcile():
                while not stopping.is_set():
                    if sessions:
                        await asyncio.to_thread(sessions.reconcile)
                    try:
                        await asyncio.wait_for(stopping.wait(), timeout=1)
                    except asyncio.TimeoutError:
                        pass

            worker = asyncio.create_task(reconcile())
            try:
                if legacy and manage_legacy:
                    async with legacy.router.lifespan_context(legacy):
                        yield
                else:
                    yield
            finally:
                await asyncio.to_thread(directory.close)
                stopping.set()
                await worker
                if sessions:
                    await asyncio.to_thread(sessions.reconcile)

    app = FastAPI(title="Scientific Forecast Extension", lifespan=lifespan)
    origins = os.getenv("FORECAST_CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
    app.add_middleware(CORSMiddleware, allow_origins=[s.strip() for s in origins.split(",") if s.strip()],
                       allow_methods=["GET", "POST"], allow_headers=["Authorization", "Content-Type"])

    def identity(request: Request, supplied: str = "local"):
        auth = request.headers.get("authorization", "")
        if host_resources is not None:
            from security.auth_dependency import get_current_user
            if not auth.startswith("Bearer "):
                raise HTTPException(401, "请使用原项目的登录凭证")
            return str(get_current_user(token=auth[7:])["user_id"])
        local_key = os.getenv("FORECAST_ACCESS_TOKEN")
        if local_key and hmac.compare_digest(auth, f"Bearer {local_key}"):
            return "local"
        if legacy and auth.startswith("Bearer "):
            try:
                from security.jwt_handler import verify_token
                return str(verify_token(auth[7:])["user_id"])
            except Exception:
                raise HTTPException(401, "登录凭证无效")
        # Unchanged legacy UI does not send Authorization on chat fetches.
        # Compatibility is restricted to loopback; remote requests must authenticate.
        loopback = request.client and request.client.host in {"127.0.0.1", "::1", "testclient"}
        if loopback and not local_key:
            return supplied if legacy else "local"
        raise HTTPException(401, "请通过 Authorization: Bearer 提交访问凭证")

    def check_thread(user, thread):
        if host_resources is not None:
            return app.state.sessions.require(user, thread)
        if legacy:
            from runtime.chat_store import ensure_thread_access
            if not ensure_thread_access(user, thread):
                raise HTTPException(403, "无权访问会话")

    def check_host_user(user, request):
        if identity(request) != user:
            raise HTTPException(403, "登录用户与会话用户不一致")

    async def delete_host_session(user, thread, request):
        check_host_user(user, request)
        if not await asyncio.to_thread(app.state.sessions.delete, user, thread):
            # This callback is also used by original host routes, outside ScientificRoute.
            raise HTTPException(409, detail=ForecastError("session_deleting").problem())

    app.state.delete_host_session = delete_host_session
    app.state.check_host_user = check_host_user

    @app.post(PREFIX + "/forecast/sessions")
    async def create_session(payload: SessionCreateRequest, request: Request):
        user = identity(request)
        if app.state.sessions is None:
            raise HTTPException(404, "仅原服务模式支持会话管理")
        metadata = await asyncio.to_thread(app.state.sessions.create, user, payload.request_id, payload.title)
        return {**metadata, "request_id": payload.request_id}

    @app.get(PREFIX + "/forecast/sessions")
    async def list_sessions(request: Request, page: int = Query(1, alias="pageNum", ge=1),
                            size: int = Query(20, alias="pageSize", ge=1, le=100)):
        user = identity(request)
        if app.state.sessions is None:
            raise HTTPException(404, "仅原服务模式支持会话管理")
        return await asyncio.to_thread(app.state.sessions.list, user, page, size)

    def conversation_state(user, thread):
        return app.state.forecast.state(user, thread) or {"params": {}, "history": [], "runs": [], "version": 0}

    @app.get(PREFIX + "/forecast/session/{thread_id}")
    async def session_snapshot(thread_id: str, request: Request, after: int = 0, limit: int = 100):
        user = identity(request)
        metadata = check_thread(user, thread_id)
        sessions = app.state.sessions
        if sessions is None or sessions.lookup(user, thread_id) is None:
            raise HTTPException(404, "预测会话不存在")
        messages = await asyncio.to_thread(sessions.history, user, thread_id, max(0, after), max(1, min(limit, 200)))
        tasks = [task_view(t) for t in app.state.store.list_tasks(session_key(user, thread_id))]
        for task in tasks:
            if task.get("artifacts"):
                task["downloads"] = links(request, task["run_id"], task["artifacts"])
        current = conversation_state(user, thread_id)
        last = current.get("response", {})
        active = next((t for t in tasks if t["status"] in {"queued", "running", "cancelling"}), None)
        task = active or next((t for t in tasks if t["run_id"] == last.get("run_id")), None)
        return {**metadata, "state": current, "messages": messages, "view": present(last, task),
                "next_after": messages[-1]["id"] if messages else after,
                "has_more": len(messages) == max(1, min(limit, 200)), "tasks": tasks}

    @app.get(PREFIX + "/forecast/tasks/{thread_id}")
    async def task_history(thread_id: str, request: Request, page: int = Query(1, alias="pageNum", ge=1),
                           size: int = Query(20, alias="pageSize", ge=1, le=100), selection: bool = False):
        user = identity(request)
        check_thread(user, thread_id)
        agent = app.state.forecast
        tasks = agent.task_history.list(session_key(user, thread_id))
        if selection:
            pending = agent.state(user, thread_id).get("pending_task") or {}
            candidates = set(pending.get("candidate_ids", []))
            tasks = [t for t in tasks if t["run_id"] in candidates]
        return {"items": [agent.task_history.summary(t) for t in tasks[(page-1)*size:page*size]],
                "total": len(tasks), "pageNum": page, "pageSize": size}

    @app.delete(PREFIX + "/forecast/session/{thread_id}")
    async def delete_session(thread_id: str, request: Request):
        user = identity(request)
        if app.state.sessions is None:
            raise HTTPException(404, "仅原服务模式支持会话管理")
        if app.state.sessions.lookup(user, thread_id) is None:
            raise HTTPException(404, "预测会话不存在")
        await delete_host_session(user, thread_id, request)
        return {"success": True}

    def links(request: Request, run_id: str, names: list[str]):
        expires = int(time.time()) + 86400
        signature = hmac.new(app.state.secret.encode(), f"{run_id}:{expires}".encode(), sha256).hexdigest()
        base = str(request.base_url).rstrip("/")
        return [dict(name=name, url=f"{base}{PREFIX}/forecast/files/{run_id}/{name}?expires={expires}&signature={signature}") for name in names]

    @app.get(PREFIX + "/forecast/health")
    async def health():
        return {"status": "ready", "model": "timesfm3", "device": "cpu",
                "dialogue": type(app.state.forecast.interpreter).__name__, "agents": app.state.agents.list()}

    @app.get(PREFIX + "/forecast/cases")
    async def cases(request: Request):
        identity(request)
        registry = app.state.forecast.workflow.registry
        entries = await asyncio.to_thread(registry.list_cases)
        modes = {c["mode"] for c in entries}
        return {"cases": entries, "horizons_hours": registry.warnings.allowed_hours([]), "max_cases": cfg.max_cases,
                "sources": [{"id": key, **value} for key, value in registry.statuses.items()],
                "frequency_minutes": cfg.frequency_minutes, "mode": next(iter(modes)) if len(modes) == 1 else "mixed"}

    @app.post(PREFIX + "/forecast/catalog/refresh")
    async def refresh_catalog(request: Request):
        identity(request)
        registry = app.state.forecast.workflow.registry
        summary = await asyncio.to_thread(registry.refresh, reload_config=True)
        return {**summary, "cases": registry.list_cases(), "max_cases": cfg.max_cases}

    @app.get(PREFIX + "/forecast/state/{thread_id}")
    async def state(thread_id: str, request: Request, user_id: str = "local"):
        user = identity(request, user_id)
        check_thread(user, thread_id)
        return conversation_state(user, thread_id)

    @app.get(PREFIX + "/forecast/cases/{case_id}")
    async def describe_case(case_id: str, request: Request):
        identity(request)
        try:
            return DataCatalog(app.state.forecast.workflow.registry).describe_series(case_id)
        except KeyError:
            raise HTTPException(404, "案例不存在")

    @app.get(PREFIX + "/forecast/events/{thread_id}")
    async def events(thread_id: str, request: Request, after: int = 0, user_id: str = "local"):
        user = identity(request, user_id)
        check_thread(user, thread_id)
        result = app.state.store.since(session_key(user, thread_id), max(0, after))
        for event in result:
            event["protocol_version"] = "1.0"
            if event.get("run_id") and event["type"] != "turn.completed":
                event["reply_id"] = "result-" + event["run_id"]
            if event.get("artifacts"):
                event["downloads"] = links(request, event["run_id"], event["artifacts"])
        return {"events": result}

    @app.get(PREFIX + "/forecast/result/{run_id}")
    async def result(run_id: str, request: Request, session_id: str | None = None,
                     thread_id: str | None = None, user_id: str = "local"):
        if not (session_id or thread_id) or (session_id and thread_id and session_id != thread_id):
            raise HTTPException(422, "请提供唯一的 session_id；thread_id 仅作为兼容字段")
        thread_id = session_id or thread_id
        user = identity(request, user_id)
        check_thread(user, thread_id)
        try:
            data = app.state.forecast.result(run_id, session_key(user, thread_id))
        except ForecastError:
            raise
        except ValueError as exc:
            raise HTTPException(404, str(exc))
        artifacts = [name for name in data.artifacts if not (data.research and data.report_status != "completed" and name.startswith("report."))]
        return {"result": data.model_dump(mode="json"), "downloads": links(request, run_id, artifacts)}

    @app.post(PREFIX + "/forecast/result/{run_id}/report")
    async def retry_report(run_id: str, request: Request, session_id: str):
        user = identity(request, "local")
        check_thread(user, session_id)
        # Ownership is checked before touching either result files or the worker.
        app.state.forecast.result(run_id, session_key(user, session_id))
        app.state.forecast.runner.retry_report(run_id, session_key(user, session_id))
        return {"run_id": run_id, "status": "pending"}

    @app.get(PREFIX + "/forecast/files/{run_id}/{filename}")
    async def artifact(run_id: str, filename: str, expires: int, signature: str):
        expected = hmac.new(app.state.secret.encode(), f"{run_id}:{expires}".encode(), sha256).hexdigest()
        if expires < time.time() or not hmac.compare_digest(signature, expected):
            raise HTTPException(403, "文件链接无效或已过期")
        task = app.state.store.task(run_id)
        if not task or task["status"] != "completed" or filename not in task.get("artifacts", []):
            raise HTTPException(404, "文件不存在")
        folder = (cfg.root / "runs" / run_id).resolve()
        path = (folder / filename).resolve()
        if not path.is_relative_to(folder) or not path.is_file():
            raise HTTPException(404, "文件不存在")
        if filename == "report.html":
            # Relative image URLs inherit a signature via a base query only if rewritten.
            from fastapi.responses import HTMLResponse
            html = path.read_text(encoding="utf-8")
            for entry in task["artifacts"]:
                if entry.endswith(".png"):
                    html = html.replace(f"src='{entry}'", f"src='{entry}?expires={expires}&signature={signature}'")
            return HTMLResponse(html, headers={"Content-Security-Policy": "default-src 'none'; img-src 'self'; style-src 'unsafe-inline'", "Referrer-Policy": "no-referrer"})
        return FileResponse(path)

    @app.post(PREFIX + "/forecast/agent/{thread_id}/{agent_id}")
    async def bind_agent(thread_id: str, agent_id: str, request: Request, user_id: str = "local"):
        user = identity(request, user_id)
        check_thread(user, thread_id)
        if agent_id != "legacy" or legacy is None:
            try:
                app.state.agents.get(agent_id)
            except ValueError as exc:
                raise HTTPException(404, str(exc))
        if any(t["status"] in {"queued", "running", "cancelling"} for t in app.state.store.list_tasks(session_key(user, thread_id))):
            raise HTTPException(409, "当前任务结束后才能切换智能体")
        app.state.store.binding(user, thread_id, agent_id)
        return {"agent_id": agent_id}

    async def handle(request: Request, stream: bool, compatibility: bool, *, fixed_agent=None):
        raw = await request.json()
        parsed = TurnInput.model_validate(raw)
        parsed.user_id = identity(request, parsed.user_id)
        if host_resources is not None and raw.get("user_id") is not None and str(raw["user_id"]) != parsed.user_id:
            raise HTTPException(403, "登录用户与会话用户不一致")
        check_thread(parsed.user_id, parsed.thread_id)
        if host_resources is not None:
            from runtime.chat_store import get_chat_files_by_message, update_thread_time
            if parsed.attachments or (parsed.message_id is not None and get_chat_files_by_message(parsed.thread_id, str(parsed.message_id))):
                raise HTTPException(422, "科学预测使用已注册数据源，请移除本轮临时附件")
            app.state.sessions.validate_message(parsed.user_id, parsed.thread_id, parsed.message_id, parsed.message)
            update_thread_time(parsed.thread_id)
        store = app.state.store
        selected = fixed_agent or store.binding(parsed.user_id, parsed.thread_id)
        if selected is None:
            selected = "forecast"
            if legacy:
                from runtime.chat_store import get_content_messages
                old = get_content_messages(parsed.thread_id)
                if any(m["role"] == "assistant" for m in old):
                    selected = "legacy"
            store.binding(parsed.user_id, parsed.thread_id, selected)
        if selected == "legacy" and legacy:
            scope = {**request.scope, "app": legacy}
            old_request = StarletteRequest(scope, request.receive)
            from routers.chat_router import ChatRequest, chat_stream, chat
            old_payload = ChatRequest(**{k: v for k, v in raw.items() if k in ChatRequest.model_fields})
            old_payload.user_id = parsed.user_id
            return await (chat_stream(old_payload, old_request) if stream else chat(old_payload, old_request))
        agent = app.state.agents.get(selected)
        if parsed.request_id is None and parsed.message_id is None:
            parsed.request_id = secrets.token_hex(16)
        replayed = selected == "forecast" and bool(store.turn(request_turn_id(parsed)))
        async def execute_turn():
            return {**await asyncio.to_thread(agent.turn, parsed), "session_id": parsed.thread_id,
                    "request_id": parsed.request_id}
        # Start the durable operation independently of the stream consumer.
        pending_turn = asyncio.create_task(execute_turn()) if stream else None
        if pending_turn:
            pending_turn.add_done_callback(lambda task: task.exception() if not task.cancelled() else None)
        response = None if stream else await execute_turn()
        if not stream and legacy and host_resources is None and not replayed:
            from runtime.chat_store import save_message
            # The original UI may already have saved this user message.
            if parsed.message_id is None:
                save_message(parsed.user_id, parsed.thread_id, "user", parsed.message)
            if not stream:
                save_message(parsed.user_id, parsed.thread_id, "assistant", response["content"])
        if not stream:
            return response
        async def generate():
            reply_id = "reply-" + request_turn_id(parsed)
            yield encode_sse({"type": "status", "stage": "started", "status": "processing",
                              "protocol_version": "1.0", "reply_id": reply_id,
                              "session_id": parsed.thread_id, "request_id": parsed.request_id})
            try:
                while not pending_turn.done():
                    try:
                        await asyncio.wait_for(asyncio.shield(pending_turn), timeout=.5)
                    except asyncio.TimeoutError:
                        yield ": keepalive\n\n"
                response = pending_turn.result()
            except Exception as exc:
                error = json.loads(http_error(exc).body)
                error.update(session_id=parsed.thread_id, request_id=parsed.request_id, reply_id=reply_id)
                yield encode_sse({**error, "type": "error"})
                yield encode_sse({**error, "type": "done"})
                return
            if legacy and host_resources is None and not replayed and parsed.message_id is None:
                from runtime.chat_store import save_message
                save_message(parsed.user_id, parsed.thread_id, "user", parsed.message)
            text = response["content"]
            if not compatibility and response.get("interaction"):
                yield encode_sse({"type": "interaction.required", "payload": response["interaction"], "message": text})
            yield encode_sse({"type": "message_delta", "delta": text + "\n\n", "reply_id": reply_id})
            run_id = response.get("run_id")
            seen = 0
            task = store.task(run_id) if run_id and selected == "forecast" else None
            while task and task["status"] in {"queued", "running", "cancelling"}:
                if await request.is_disconnected():
                    return  # Prediction continues in the worker.
                for event in store.since(session_key(parsed.user_id, parsed.thread_id), seen):
                    seen = event["event_id"]
                    if event.get("run_id") != run_id or event["type"] not in {"task.progress", "task.stalled", "data.ready"}:
                        continue
                    if not compatibility:
                        yield encode_sse({**event, "reply_id": "result-" + run_id})
                    elif event["status"] == "running":
                        yield encode_sse({"type": "agent_event", "nodes": [LABELS.get(event["stage"], event["stage"])]})
                yield ": keepalive\n\n"
                await asyncio.sleep(.5)
                task = store.task(run_id)
                if task and task.get("stalled"):
                    break  # Stop keeping the browser open forever; the task itself is still stopping.
            if task and task["status"] == "completed":
                try:
                    result = agent.result(run_id, session_key(parsed.user_id, parsed.thread_id))
                except ForecastError as exc:
                    failure = present({**response, "content": str(exc), "error": True, "problem": exc.problem()}, task)
                    yield encode_sse({**failure, "type": "error"})
                    yield encode_sse({**failure, "type": "done"})
                    return
                from .feedback import completion_message
                if response.get("artifacts") is None:
                    text += "\n\n" + completion_message(result)
                downloads = links(request, run_id, result.artifacts)
                if not compatibility:
                    yield encode_sse({"type": "result.ready", "run_id": run_id, "downloads": downloads,
                                      "content": completion_message(result), "reply_id": "result-" + run_id,
                                      "warning_analysis": result.warning_analysis.model_dump(mode="json") if result.warning_analysis else None,
                                      "task": task_view(task), "protocol_version": "1.0"})
                if task.get("analysis_status") == "pending":
                    yield encode_sse({"type": "analysis.progress", "run_id": run_id, "status": "pending",
                                      "message": "预测已完成，正在结合领域背景生成分析。", "reply_id": "result-" + run_id})
                    while task and task.get("analysis_status") == "pending":
                        if await request.is_disconnected():
                            return
                        yield ": keepalive\n\n"
                        await asyncio.sleep(.5)
                        task = store.task(run_id)
                    if task and task["status"] == "completed":
                        result = agent.result(run_id, session_key(parsed.user_id, parsed.thread_id))
                        downloads = links(request, run_id, result.artifacts)
                        yield encode_sse({"type": "analysis.ready" if task.get("analysis_status") != "unavailable" else "analysis.unavailable",
                            "run_id": run_id, "status": task.get("analysis_status"), "reply_id": "result-" + run_id,
                            "warning_analysis": result.warning_analysis.model_dump(mode="json") if result.warning_analysis else None,
                            "content": completion_message(result), "downloads": downloads, "task": task_view(task), "protocol_version": "1.0"})
                        if compatibility:
                            text = response["content"] + "\n\n" + completion_message(result)
            elif task and task["status"] in {"failed", "cancelled", "interrupted"}:
                text += "\n\n" + task.get("error", "任务未完成")
                if not compatibility:
                    yield encode_sse({"type": "task.failed", "run_id": run_id, "status": task["status"],
                        "content": "任务状态：" + task["status"] + "。" + task.get("error", ""),
                        "problem": task.get("problem"), "task": task_view(task),
                        "reply_id": "result-" + run_id, "protocol_version": "1.0"})
            if legacy and host_resources is None and not replayed:
                from runtime.chat_store import save_message
                save_message(parsed.user_id, parsed.thread_id, "assistant", text)
            if not compatibility:
                text = response["content"]  # Result messages have their own stable result-<run_id> identity.
            yield encode_sse({"type": "message", "content": text, "reply_id": reply_id})
            yield encode_sse({**present(response, task), "type": "done", "content": text})
        return StreamingResponse(generate(), media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

    @app.post(PREFIX + "/forecast/chat/stream")
    async def forecast_chat(request: Request):
        return await handle(request, True, False, fixed_agent="forecast")

    @app.post(PREFIX + "/forecast/chat")
    async def forecast_chat_once(request: Request):
        return await handle(request, False, False, fixed_agent="forecast")

    @app.post(PREFIX + "/forecast/turn")
    async def turn(request: Request):
        return await handle(request, False, False, fixed_agent="forecast")

    @app.post(PREFIX + "/chat/stream")
    async def compatible_chat(request: Request):
        return await handle(request, True, True)

    @app.post(PREFIX + "/chat")
    async def compatible_turn(request: Request):
        return await handle(request, False, True)

    @app.exception_handler(Exception)
    @app.exception_handler(HTTPException)
    @app.exception_handler(ValueError)
    async def invalid_request(request, exc):
        return http_error(exc)

    if legacy and manage_legacy:
        app.mount("/", legacy)
    return app
