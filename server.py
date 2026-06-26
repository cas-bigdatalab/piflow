import json
import logging
import os
import uuid
from datetime import datetime
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from infra.config_loader import get_settings
from infra.logging import init_logging
from routers.subagent.workflow_advisor import workflow_advisor_router
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
from services.object_storage_service import ObjectStorageService

from routers.auth_router import router as auth_router
from routers.dag_panel_api import router as dag_router
from routers.dag_runtime_api import router as dag_runtime_router
from routers.user_router import router as user_router
from routers.subagent.workflow_advisor.workflow_advisor_router import router as workflow_advisor_router

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
        engine = getattr(app.state, "piflow_engine", None)
        if engine is None:
            return
        await engine.shutdown()


app = FastAPI(lifespan=lifespan)

app.include_router(auth_router)
app.include_router(dag_router)
app.include_router(dag_runtime_router)
app.include_router(user_router)
app.include_router(workflow_advisor_router)

STORAGE_DIR.mkdir(parents=True, exist_ok=True)

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


class AttachmentItem(BaseModel):
    path: str
    name: str


class AttachMessageFilesRequest(BaseModel):
    user_id: str
    thread_id: str
    message_id: int
    attachments: list[AttachmentItem]


class SaveStorageFileRequest(BaseModel):
    user_id: str
    target_path: str
    local_path: str


class ListStorageFilesRequest(BaseModel):
    user_id: str
    dir_path: str = ""


class ListUserWorkspaceRequest(BaseModel):
    user_id: str
    dir_path: str = ""


def get_engine(request: Request) -> AgentEngine:
    engine = getattr(request.app.state, "piflow_engine", None)
    if engine is None:
        raise HTTPException(status_code=503, detail="agent piflow_engine is not initialized")
    return engine


def _resolve_user_directory(
    workspace: WorkspaceManager,
    user_id: str,
    dir_path: str,
    *,
    create: bool = False,
) -> Path:
    normalized_user_id = user_id.strip()
    if not normalized_user_id:
        raise HTTPException(status_code=400, detail="user_id is required")

    try:
        workspace.ensure_user_workspace(normalized_user_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    raw_dir = (dir_path or "").strip()
    user_root = workspace.get_user_root(normalized_user_id).resolve()

    if not raw_dir or raw_dir in {".", "/"}:
        resolved_dir = user_root
    else:
        try:
            resolved_dir = workspace.resolve_user_virtual_path(
                normalized_user_id,
                raw_dir,
                create_parent=create,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    try:
        resolved_dir.relative_to(user_root)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="directory escapes user workspace") from exc

    if create:
        resolved_dir.mkdir(parents=True, exist_ok=True)

    return resolved_dir


def _build_user_workspace_path(workspace: WorkspaceManager, user_id: str, path: Path) -> str:
    user_root = workspace.get_user_root(user_id).resolve()
    relative = path.resolve().relative_to(user_root)
    return "/" + "/".join(relative.parts)


def _serialize_user_directory_entry(
    workspace: WorkspaceManager,
    user_id: str,
    entry: Path,
) -> dict[str, object]:
    stat = entry.stat()
    entry_type = "directory" if entry.is_dir() else "file"
    return {
        "name": entry.name,
        "path": _build_user_workspace_path(workspace, user_id, entry),
        "type": entry_type,
        "size": None if entry.is_dir() else stat.st_size,
        "last_modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
    }


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


@app.post("/message/attach")
async def attach_message_files_api(req: AttachMessageFilesRequest):
    user_id = req.user_id.strip()
    thread_id = req.thread_id.strip()
    message_id = str(req.message_id).strip()

    if not user_id:
        raise HTTPException(status_code=400, detail="user_id is required")
    if not thread_id:
        raise HTTPException(status_code=400, detail="thread_id is required")
    if not message_id:
        raise HTTPException(status_code=400, detail="message_id is required")
    if not req.attachments:
        return {"attachments": []}

    workspace = WorkspaceManager()
    try:
        workspace.ensure_user_workspace(user_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    allowed = {t["thread_id"] for t in get_user_threads(user_id)}
    if thread_id not in allowed:
        raise HTTPException(status_code=403, detail="thread not found or access denied")

    attached = []
    for item in req.attachments:
        path = item.path.strip()
        name = item.name.strip()

        if not path:
            raise HTTPException(status_code=400, detail="attachment path is required")
        if not name:
            raise HTTPException(status_code=400, detail="attachment name is required")

        try:
            source = workspace.resolve_user_virtual_path(user_id, path)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        if not source.exists() or not source.is_file():
            raise HTTPException(status_code=404, detail="attachment file not found")

        record = save_chat_file(
            user_id=user_id,
            thread_id=thread_id,
            message_id=message_id,
            virtual_path=workspace.to_user_relative_path(user_id, path),
            original_filename=name,
        )
        if record:
            attached.append({
                "file_id": record.get("file_id"),
                "path": record.get("virtual_path"),
                "name": record.get("original_filename"),
            })

    return {"attachments": attached}


@app.post("/workspace/upload")
async def upload_workspace_file(
    user_id: str = Form(...),
    thread_id: str = Form(...),
    message_id: str = Form(...),
    file: UploadFile = File(...),
):
    workspace = WorkspaceManager()
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

    try:
        workspace.ensure_user_workspace(normalized_user_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    virtual_path = f"/temp/{safe_thread_id}/{safe_message_id}_{safe_name}"

    try:
        destination = workspace.resolve_user_virtual_path(
            normalized_user_id,
            virtual_path,
            create_parent=True,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    content = await file.read()
    destination.write_bytes(content)
    saved_virtual_path = workspace.to_user_relative_path(normalized_user_id, virtual_path)
    record = save_chat_file(
        user_id=normalized_user_id,
        thread_id=safe_thread_id,
        message_id=safe_message_id,
        virtual_path=saved_virtual_path,
        original_filename=safe_name,
    )

    return {
        "file_id": record["file_id"] if record else None,
        "user_id": normalized_user_id,
        "thread_id": safe_thread_id,
        "message_id": safe_message_id,
        "path": saved_virtual_path,
        "original_filename": safe_name,
        "size": len(content),
        "content_type": file.content_type,
    }


@app.post("/workspace/list")
async def list_user_workspace(req: ListUserWorkspaceRequest):
    workspace = WorkspaceManager()
    user_id = req.user_id.strip()
    directory = _resolve_user_directory(workspace, user_id, req.dir_path)

    if not directory.exists():
        raise HTTPException(status_code=404, detail="directory not found")
    if not directory.is_dir():
        raise HTTPException(status_code=400, detail="path is not a directory")

    user_root = workspace.get_user_root(user_id).resolve()
    relative_dir = directory.relative_to(user_root)
    display_dir_path = "/" + "/".join(relative_dir.parts) if relative_dir.parts else ""

    entries = sorted(
        directory.iterdir(),
        key=lambda item: (not item.is_dir(), item.name.lower()),
    )

    return {
        "user_id": user_id,
        "dir_path": display_dir_path,
        "items": [
            _serialize_user_directory_entry(workspace, user_id, entry)
            for entry in entries
        ],
    }


@app.post("/workspace/upload/path")
async def upload_user_workspace_file(
    user_id: str = Form(...),
    dir_path: str = Form(""),
    file: UploadFile = File(...),
):
    workspace = WorkspaceManager()
    normalized_user_id = user_id.strip()
    safe_name = Path(file.filename or "").name.strip()

    if not normalized_user_id:
        raise HTTPException(status_code=400, detail="user_id is required")
    if not safe_name:
        raise HTTPException(status_code=400, detail="filename is required")

    target_dir = _resolve_user_directory(workspace, normalized_user_id, dir_path, create=True)
    destination = (target_dir / safe_name).resolve()

    user_root = workspace.get_user_root(normalized_user_id).resolve()
    try:
        destination.relative_to(user_root)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="file path escapes user workspace") from exc

    content = await file.read()
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(content)

    relative_path = "/" + "/".join(destination.relative_to(user_root).parts)
    return {
        "user_id": normalized_user_id,
        "dir_path": dir_path.strip(),
        "path": relative_path,
        "original_filename": safe_name,
        "size": len(content),
        "content_type": file.content_type,
    }


@app.get("/workspace/download")
async def download_workspace_file(user_id: str, path: str):
    workspace = WorkspaceManager()
    try:
        workspace.ensure_user_workspace(user_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    try:
        source = workspace.resolve_user_virtual_path(user_id, path)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if not source.exists() or not source.is_file():
        raise HTTPException(status_code=404, detail="file not found")

    return FileResponse(
        path=source,
        filename=source.name,
        media_type="application/octet-stream",
    )


@app.post("/storage/save")
async def save_storage_file(req: SaveStorageFileRequest):
    service = ObjectStorageService()

    try:
        result = service.save_local_file(
            user_id=req.user_id,
            target_path=req.target_path,
            local_path=req.local_path,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception:
        log.exception(
            "failed to save local file to object storage user_id=%s target_path=%s local_path=%s",
            req.user_id,
            req.target_path,
            req.local_path,
        )
        raise HTTPException(status_code=500, detail="failed to save file to object storage")

    return result


@app.post("/storage/list")
async def list_storage_files(req: ListStorageFilesRequest):
    service = ObjectStorageService()

    try:
        result = service.list_directory(
            user_id=req.user_id,
            dir_path=req.dir_path,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception:
        log.exception(
            "failed to list object storage directory user_id=%s dir_path=%s",
            req.user_id,
            req.dir_path,
        )
        raise HTTPException(status_code=500, detail="failed to list object storage directory")

    return result


app.mount("/storage", StaticFiles(directory=STORAGE_DIR), name="storage")


# @app.get("/skills/list")
# async def list_skills_api(
#     page: int = 1, page_size: int = 20, keyword: str = "", type: str = ""
# ):
#     try:
#         offset = (page - 1) * page_size
#         result = list_skills(limit=page_size, offset=offset, keyword=keyword, type=type)
#
#         data = []
#         for r in result.get("data", []):
#             if not r:
#                 continue
#             data.append(
#                 {
#                     "name": r.get("name"),
#                     "description": r.get("description"),
#                     "icon": r.get("icon_path"),
#                     "version": r.get("version"),
#                     "type": r.get("type"),
#                 }
#             )
#
#         return {
#             "code": 200,
#             "data": data,
#             "total": result.get("total", 0),
#             "current_count": len(data),
#         }
#     except Exception as exc:
#         log.error("failed to get skills list: %s", exc)
#         return {
#             "code": 500,
#             "data": [],
#             "total": 0,
#             "current_count": 0,
#             "message": str(exc),
#         }
#
#
# @app.get("/skills/types")
# async def get_skills_types():
#     try:
#         types = get_skills_grouped_by_type()
#         return {
#             "code": 200,
#             "data": types,
#             "total": len(types),
#         }
#     except Exception as exc:
#         log.error("failed to get skills types: %s", exc)
#         return {
#             "code": 500,
#             "data": [],
#             "total": 0,
#             "message": str(exc),
#         }


if __name__ == "__main__":
    init_logging()
    settings = get_settings()
    enable_reload = os.getenv("FLOW_API_RELOAD", "").lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    port = settings.app.port

    if enable_reload:
        log.info("starting uvicorn with reload enabled on port %s", port)
        uvicorn.run(
            "server:app",
            host="0.0.0.0",
            port=port,
            reload=True,
        )
    else:
        log.info("starting uvicorn without reload on port %s", port)
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=port,
            reload=False,
        )
