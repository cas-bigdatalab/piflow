import json
import logging
import os
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from infra.logging import init_logging
from runtime.chat_store import (
    create_thread,
    delete_thread,
    get_chat_files,
    get_messages,
    get_user_threads,
    list_skills,
    save_chat_file,
    save_message,
    update_thread_time,
)
from runtime.engine import AgentEngine
from runtime.skill_manage import (
    get_skills_grouped_by_type,
)
from runtime.workspace_manager import WorkspaceManager


log = logging.getLogger("flow.api")
PROJECT_ROOT = Path(__file__).resolve().parent
STORAGE_DIR = PROJECT_ROOT / "storage"


def _preview_text(value: str, limit: int = 120) -> str:
    text = value.replace("\r", " ").replace("\n", " ").strip()
    if len(text) <= limit:
        return text
    return text[:limit] + "..."


def _encode_sse(data: dict, event: str | None = None) -> str:
    lines = []
    if event:
        lines.append(f"event: {event}")

    payload = json.dumps(data, ensure_ascii=False)
    for line in payload.splitlines() or [""]:
        lines.append(f"data: {line}")

    return "\n".join(lines) + "\n\n"


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_logging()
    log.info("starting API mode")

    engine = AgentEngine()
    await engine.initialize()
    app.state.engine = engine

    log.info("DeepAgent server started")
    try:
        yield
    finally:
        engine = getattr(app.state, "engine", None)
        if engine is None:
            return
        await engine.shutdown()


app = FastAPI(lifespan=lifespan)
STORAGE_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/storage", StaticFiles(directory=STORAGE_DIR), name="storage")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str
    thread_id: str = "default"
    user_id: str = "default_user"
    attachments: list[str] = []
    message_id: int | None = None


class ThreadListRequest(BaseModel):
    user_id: str


class DeleteThreadRequest(BaseModel):
    user_id: str
    thread_id: str


class ThreadMessagesRequest(BaseModel):
    user_id: str
    thread_id: str
    limit: int = 200


class CreateMessageRequest(BaseModel):
    user_id: str
    thread_id: str
    content: str
    role: str = "user"


def get_engine(request: Request) -> AgentEngine:
    engine = getattr(request.app.state, "engine", None)
    if engine is None:
        raise HTTPException(status_code=503, detail="agent engine is not initialized")
    return engine


@app.post("/chat")
async def chat(req: ChatRequest, request: Request):
    engine = get_engine(request)
    request_id = uuid.uuid4().hex[:8]

    log.info(
        "chat request received request_id=%s thread_id=%s user_id=%s input_chars=%s preview=%s",
        request_id,
        req.thread_id,
        req.user_id,
        len(req.message),
        _preview_text(req.message),
    )

    try:
        result = await engine.run(
            req.message,
            req.thread_id,
            req.user_id,
            attachments=req.attachments,
            request_id=request_id,
            message_id=req.message_id,
        )
    except Exception:
        log.exception(
            "chat request failed request_id=%s thread_id=%s user_id=%s",
            request_id,
            req.thread_id,
            req.user_id,
        )
        raise

    log.info(
        "chat request completed request_id=%s thread_id=%s user_id=%s answer_chars=%s",
        request_id,
        req.thread_id,
        req.user_id,
        len(result),
    )
    return {"events": result}


@app.post("/chat/stream")
async def chat_stream(req: ChatRequest, request: Request):
    engine = get_engine(request)
    request_id = uuid.uuid4().hex[:8]

    log.info(
        "chat stream request received request_id=%s thread_id=%s user_id=%s input_chars=%s preview=%s",
        request_id,
        req.thread_id,
        req.user_id,
        len(req.message),
        _preview_text(req.message),
    )

    async def event_generator():
        try:
            async for event in engine.stream_chat(
                req.message,
                req.thread_id,
                req.user_id,
                attachments=req.attachments,
                request_id=request_id,
                message_id=req.message_id,
            ):
                yield _encode_sse(event, event.get("type"))
        except Exception as exc:
            log.exception(
                "chat stream request failed request_id=%s thread_id=%s user_id=%s",
                request_id,
                req.thread_id,
                req.user_id,
            )
            yield _encode_sse(
                {
                    "type": "error",
                    "request_id": request_id,
                    "message": str(exc),
                },
                "error",
            )
        else:
            log.info(
                "chat stream request completed request_id=%s thread_id=%s user_id=%s",
                request_id,
                req.thread_id,
                req.user_id,
            )

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.post("/threads/getTitles")
async def get_threads(req: ThreadListRequest):
    threads = get_user_threads(req.user_id)
    return {"threads": threads}


@app.post("/thread/delete")
async def delete_thread_api(req: DeleteThreadRequest):
    delete_thread(req.user_id, req.thread_id)
    return {"success": True}


@app.post("/thread/messages")
async def thread_messages(req: ThreadMessagesRequest):
    allowed = {t["thread_id"] for t in get_user_threads(req.user_id)}
    if req.thread_id not in allowed:
        raise HTTPException(status_code=403, detail="thread not found or access denied")
    messages = get_messages(req.thread_id, limit=req.limit)
    attachment_rows = get_chat_files(req.thread_id)
    attachments_by_message: dict[int, list[dict[str, object]]] = {}
    for row in attachment_rows:
        try:
            message_id = int(row.get("message_id"))
        except (TypeError, ValueError):
            continue

        attachments_by_message.setdefault(message_id, []).append({
            "file_id": row.get("file_id"),
            "path": row.get("virtual_path"),
            "name": row.get("original_filename"),
        })

    for message in messages:
        message["attachments"] = attachments_by_message.get(message["id"], [])

    return {"messages": messages}


@app.post("/message/create")
async def create_message_api(req: CreateMessageRequest):
    user_id = req.user_id.strip()
    thread_id = req.thread_id.strip()
    content = req.content.strip()
    role = req.role.strip() or "user"

    if not user_id:
        raise HTTPException(status_code=400, detail="user_id is required")
    if not thread_id:
        raise HTTPException(status_code=400, detail="thread_id is required")
    if not content:
        raise HTTPException(status_code=400, detail="content is required")
    if role not in {"user", "assistant"}:
        raise HTTPException(status_code=400, detail="role must be user or assistant")

    thread_exists = bool(get_messages(thread_id, limit=1))
    if not thread_exists:
        create_thread(user_id, thread_id, content[:30])
    update_thread_time(thread_id)

    message = save_message(user_id, thread_id, role, content)
    if not message:
        raise HTTPException(status_code=500, detail="failed to create message")

    return {"message": message}


@app.post("/workspace/upload")
async def upload_workspace_file(
    user_id: str = Form(...),
    thread_id: str = Form(...),
    message_id: str = Form(...),
    file: UploadFile = File(...),
):
    workspace = WorkspaceManager()
    workspace.ensure_workspace()

    normalized_user_id = user_id.strip()
    safe_thread_id = Path(thread_id.strip()).name
    safe_message_id = Path(message_id.strip()).name
    safe_name = Path(file.filename or "").name.strip()

    if not normalized_user_id:
        raise HTTPException(status_code=400, detail="user_id is required")
    if not safe_thread_id:
        raise HTTPException(status_code=400, detail="thread_id is required")
    if not safe_message_id:
        raise HTTPException(status_code=400, detail="message_id is required")
    if not safe_name:
        raise HTTPException(status_code=400, detail="filename is required")

    virtual_path = f"/temp/{safe_thread_id}/{safe_message_id}_{safe_name}"

    try:
        destination = workspace.resolve_virtual_path(virtual_path, create_parent=True)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    content = await file.read()
    destination.write_bytes(content)
    record = save_chat_file(
        user_id=normalized_user_id,
        thread_id=safe_thread_id,
        message_id=safe_message_id,
        virtual_path=virtual_path,
        original_filename=safe_name,
    )

    return {
        "file_id": record["file_id"] if record else None,
        "user_id": normalized_user_id,
        "thread_id": safe_thread_id,
        "message_id": safe_message_id,
        "path": virtual_path,
        "original_filename": safe_name,
        "size": len(content),
        "content_type": file.content_type,
    }


@app.get("/workspace/download")
async def download_workspace_file(path: str):
    workspace = WorkspaceManager()
    workspace.ensure_workspace()

    try:
        source = workspace.resolve_virtual_path(path)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if not source.exists() or not source.is_file():
        raise HTTPException(status_code=404, detail="file not found")

    return FileResponse(
        path=source,
        filename=source.name,
        media_type="application/octet-stream",
    )


@app.get("/skills/list")
async def list_skills_api(
    page: int = 1, page_size: int = 20, keyword: str = "", type: str = ""
):
    try:
        offset = (page - 1) * page_size
        result = list_skills(limit=page_size, offset=offset, keyword=keyword, type=type)

        data = []
        for r in result.get("data", []):
            if not r:
                continue
            data.append(
                {
                    "name": r.get("name"),
                    "description": r.get("description"),
                    "icon": r.get("icon_path"),
                    "version": r.get("version"),
                    "type": r.get("type"),
                }
            )

        return {
            "code": 200,
            "data": data,
            "total": result.get("total", 0),
            "current_count": len(data),
        }
    except Exception as exc:
        log.error("failed to get skills list: %s", exc)
        return {
            "code": 500,
            "data": [],
            "total": 0,
            "current_count": 0,
            "message": str(exc),
        }


@app.get("/skills/types")
async def get_skills_types():
    try:
        types = get_skills_grouped_by_type()
        return {
            "code": 200,
            "data": types,
            "total": len(types),
        }
    except Exception as exc:
        log.error("failed to get skills types: %s", exc)
        return {
            "code": 500,
            "data": [],
            "total": 0,
            "message": str(exc),
        }


if __name__ == "__main__":
    init_logging()
    enable_reload = os.getenv("FLOW_API_RELOAD", "").lower() in {
        "1",
        "true",
        "yes",
        "on",
    }

    if enable_reload:
        log.info("starting uvicorn with reload enabled")
        uvicorn.run(
            "server:app",
            host="0.0.0.0",
            port=8080,
            reload=True,
        )
    else:
        log.info("starting uvicorn without reload")
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8080,
            reload=False,
        )
