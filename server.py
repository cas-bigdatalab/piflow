import json
import logging
import os
import shutil
import uuid
import zipfile
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
from piflow_engine.cn.piflow.engine.datasource import DataspaceError, DataspaceSource
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
from runtime.planner_engine import PlannerEngine
from runtime.skill_manage import (
    get_skills_grouped_by_type,
)
from runtime.workspace_manager import WorkspaceManager
from services.dataspace_source_service import (
    create_dataspace_source,
    delete_dataspace_source,
    get_dataspace_source,
    list_dataspace_source_directory,
    list_registered_dataspace_sources,
    update_dataspace_source,
    validate_dataspace_source_connection,
    validate_registered_dataspace_source,
)
from services.datasource_catalog_service import (
    get_datasource_catalog_detail,
    list_datasource_catalog,
)
from repositories.datasource_catalog_repository import initialize_datasource_catalog_schema
from services.object_storage_service import ObjectStorageService

from routers.auth_router import router as auth_router
from routers.community_router import router as community_router
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

    initialize_datasource_catalog_schema()
    engine = AgentEngine()
    planner_engine = PlannerEngine()
    await engine.initialize()
    await planner_engine.initialize()
    app.state.engine = engine
    app.state.planner_engine = planner_engine

    log.info("DeepAgent server started")
    try:
        yield
    finally:
        planner_engine = getattr(app.state, "planner_engine", None)
        if planner_engine is not None:
            await planner_engine.shutdown()

        engine = getattr(app.state, "engine", None)
        if engine is not None:
            await engine.shutdown()


app = FastAPI(lifespan=lifespan)

app.include_router(auth_router)
app.include_router(community_router)
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


class SaveJuicefsFileRequest(BaseModel):
    user_id: str
    target_path: str
    local_path: str


class ListJuicefsFilesRequest(BaseModel):
    user_id: str
    dir_path: str = ""


class CreateJuicefsDirectoryRequest(BaseModel):
    user_id: str
    dir_path: str


class ListUserWorkspaceRequest(BaseModel):
    user_id: str
    dir_path: str = ""
    page: int | None = None
    page_size: int | None = None


class CreateUserWorkspaceDirectoryRequest(BaseModel):
    user_id: str
    dir_path: str


class DeleteUserWorkspacePathRequest(BaseModel):
    user_id: str
    path: str


class BatchDeleteUserWorkspaceRequest(BaseModel):
    user_id: str
    paths: list[str]


class BatchDownloadUserWorkspaceRequest(BaseModel):
    user_id: str
    paths: list[str]


class MoveWorkspaceTempFilesRequest(BaseModel):
    user_id: str


class CreateDataspaceSourceRequest(BaseModel):
    name: str
    base_url: str
    app_id: str
    auth_code: str
    space_name: str
    ftp_user: str
    ftp_password: str
    logo: str = ""


class UpdateDataspaceSourceRequest(CreateDataspaceSourceRequest):
    source_id: str


class DataspaceSourceDetailRequest(BaseModel):
    source_id: str


class DataspaceSourceDirectoryListRequest(BaseModel):
    source_id: str
    path: str = ""


class ValidateDataspaceSourceRequest(BaseModel):
    base_url: str
    app_id: str
    auth_code: str
    space_name: str
    ftp_user: str
    ftp_password: str


class ValidateRegisteredDataspaceSourceRequest(BaseModel):
    source_id: str


class DatasourceCatalogDetailRequest(BaseModel):
    type_code: str


def get_engine(request: Request) -> AgentEngine:
    engine = getattr(request.app.state, "engine", None)
    if engine is None:
        raise HTTPException(status_code=503, detail="agent engine is not initialized")
    return engine


def get_planner_engine(request: Request) -> PlannerEngine:
    engine = getattr(request.app.state, "planner_engine", None)
    if engine is None:
        raise HTTPException(status_code=503, detail="planner agent is not initialized")
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


def _resolve_user_workspace_path(
    workspace: WorkspaceManager,
    user_id: str,
    path: str,
) -> Path:
    normalized_user_id = user_id.strip()
    if not normalized_user_id:
        raise HTTPException(status_code=400, detail="user_id is required")

    try:
        workspace.ensure_user_workspace(normalized_user_id)
        resolved = workspace.resolve_user_virtual_path(normalized_user_id, path)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    user_root = workspace.get_user_root(normalized_user_id).resolve()
    try:
        resolved.relative_to(user_root)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="path escapes user workspace") from exc

    return resolved


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


def _delete_user_workspace_path(
    workspace: WorkspaceManager,
    user_id: str,
    path: str,
    *,
    expect_type: str | None = None,
) -> dict[str, object]:
    target = _resolve_user_workspace_path(workspace, user_id, path)

    if not target.exists():
        raise HTTPException(status_code=404, detail="path not found")

    actual_type = "directory" if target.is_dir() else "file"
    if expect_type and actual_type != expect_type:
        raise HTTPException(status_code=400, detail=f"path is not a {expect_type}")

    relative_path = _build_user_workspace_path(workspace, user_id, target)
    if target.is_dir():
        shutil.rmtree(target)
    else:
        target.unlink()

    return {
        "path": relative_path,
        "type": actual_type,
    }


def _resolve_user_workspace_download_targets(
    workspace: WorkspaceManager,
    user_id: str,
    paths: list[str],
) -> list[Path]:
    if not user_id.strip():
        raise HTTPException(status_code=400, detail="user_id is required")
    if not paths:
        raise HTTPException(status_code=400, detail="paths is required")

    resolved_targets: list[Path] = []
    seen: set[Path] = set()
    user_root = workspace.get_user_root(user_id).resolve()
    for raw_path in paths:
        target = _resolve_user_workspace_path(workspace, user_id, raw_path)
        if target == user_root:
            raise HTTPException(status_code=400, detail="user workspace root path is not allowed")
        if not target.exists():
            raise HTTPException(status_code=404, detail=f"path not found: {raw_path}")
        if target in seen:
            continue
        seen.add(target)
        resolved_targets.append(target)

    return resolved_targets


def _add_path_to_zip(
    zip_file: zipfile.ZipFile,
    source: Path,
    arcname: str,
) -> None:
    normalized_arcname = arcname.strip("/")
    if source.is_dir():
        directory_name = f"{normalized_arcname}/" if normalized_arcname else ""
        if directory_name:
            zip_info = zipfile.ZipInfo(directory_name)
            zip_file.writestr(zip_info, "")

        for child in sorted(source.iterdir(), key=lambda item: (not item.is_dir(), item.name.lower())):
            child_arcname = f"{normalized_arcname}/{child.name}" if normalized_arcname else child.name
            _add_path_to_zip(zip_file, child, child_arcname)
        return

    zip_file.write(source, arcname=normalized_arcname)


def _build_user_workspace_download_zip(
    workspace: WorkspaceManager,
    user_id: str,
    targets: list[Path],
) -> tuple[Path, str]:
    downloads_dir = _resolve_user_directory(workspace, user_id, "/temp/downloads", create=True)
    archive_id = uuid.uuid4().hex
    if len(targets) == 1 and targets[0].is_dir():
        download_name = f"{targets[0].name}.zip"
    else:
        download_name = f"workspace_batch_{archive_id[:8]}.zip"

    zip_path = downloads_dir / f"{archive_id}.zip"
    user_root = workspace.get_user_root(user_id).resolve()
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for target in targets:
            if len(targets) == 1 and target.is_dir():
                arcname = target.name
            else:
                arcname = str(target.relative_to(user_root)).replace("\\", "/")
            _add_path_to_zip(zip_file, target, arcname)

    return zip_path, download_name


def _mask_secret(value: str) -> str:
    if not value:
        return ""
    if len(value) <= 6:
        return "*" * len(value)
    return f"{value[:3]}***{value[-2:]}"


def _serialize_dataspace_source(source: DataspaceSource) -> dict[str, object]:
    return {
        "source_id": source.source_id,
        "name": source.name,
        "base_url": source.base_url,
        "app_id": source.app_id,
        "auth_code_masked": _mask_secret(source.auth_code),
        "space_name": source.space_name,
        "space_id": source.space_id,
        "ftp_user": source.ftp_user,
        "ftp_password_masked": _mask_secret(source.ftp_password),
        "ftp_link": source.ftp_link,
        "webdav_link": source.webdav_link,
        "root_path": source.root_path,
        "logo": source.logo,
        "created_at": source.created_at.isoformat() if source.created_at else None,
        "updated_at": source.updated_at.isoformat() if source.updated_at else None,
    }


def _serialize_dataspace_source_list_item(source: DataspaceSource) -> dict[str, object]:
    return {
        "source_id": source.source_id,
        "name": source.name,
        "base_url": source.base_url,
        "database_name": source.space_name,
        "logo": source.logo,
        "created_at": source.created_at.isoformat() if source.created_at else None,
        "updated_at": source.updated_at.isoformat() if source.updated_at else None,
        "type_code": "dataspace",
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


@app.post("/planner/chat")
async def planner_chat(req: ChatRequest, request: Request):
    engine = get_planner_engine(request)
    request_id = uuid.uuid4().hex[:8]
    result = await engine.run(
        req.message,
        req.thread_id,
        req.user_id,
        attachments=req.attachments,
        request_id=request_id,
    )
    return {"events": result}


@app.post("/planner/chat/stream")
async def planner_chat_stream(req: ChatRequest, request: Request):
    engine = get_planner_engine(request)
    request_id = uuid.uuid4().hex[:8]

    async def event_generator():
        try:
            async for event in engine.stream_chat(
                req.message,
                req.thread_id,
                req.user_id,
                attachments=req.attachments,
                request_id=request_id,
            ):
                yield _encode_sse(event, event.get("type"))
        except Exception as exc:
            log.exception("planner stream request failed request_id=%s", request_id)
            yield _encode_sse(
                {"type": "error", "request_id": request_id, "message": str(exc)},
                "error",
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
            message = req.message

            if req.attachments:
                attachment_desc = "\n".join(
                    f"- {path}" for path in req.attachments
                )

                message += f"""

            以下是用户上传的输入资源，仅作为 规划 DAG Workflow 输入资源引用。

            请注意：

            1. 不需要读取这些文件内容。
            2. 仅将这些路径作为输入节点(source_stop)的 file_path 等参数使用。
            3. Workflow 中如果需要引用输入文件，请直接引用这些路径。

            上传文件：
            {attachment_desc}
            """

            async for event in engine.stream_chat(
                message,
                req.thread_id,
                req.user_id,
                attachments=[],
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
            log.info(f"attachment path {source.resolve()} is not a file")
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
    items = [
        _serialize_user_directory_entry(workspace, user_id, entry)
        for entry in entries
    ]

    result = {
        "user_id": user_id,
        "dir_path": display_dir_path,
        "items": items,
    }

    if req.page is None and req.page_size is None:
        return result

    if req.page is None or req.page_size is None:
        raise HTTPException(status_code=400, detail="page and page_size must be provided together")
    if req.page <= 0:
        raise HTTPException(status_code=400, detail="page must be greater than 0")
    if req.page_size <= 0:
        raise HTTPException(status_code=400, detail="page_size must be greater than 0")

    total = len(items)
    start = (req.page - 1) * req.page_size
    end = start + req.page_size
    paged_items = items[start:end]
    result["items"] = paged_items
    result["pagination"] = {
        "page": req.page,
        "page_size": req.page_size,
        "total": total,
        "total_pages": (total + req.page_size - 1) // req.page_size,
        "has_more": end < total,
    }
    return result


@app.post("/workspace/mkdir")
async def create_user_workspace_directory(req: CreateUserWorkspaceDirectoryRequest):
    workspace = WorkspaceManager()
    user_id = req.user_id.strip()
    target_dir = _resolve_user_workspace_path(workspace, user_id, req.dir_path)

    if target_dir.exists() and not target_dir.is_dir():
        raise HTTPException(status_code=400, detail="path already exists and is not a directory")

    target_dir.mkdir(parents=True, exist_ok=True)
    return {
        "user_id": user_id,
        "dir_path": _build_user_workspace_path(workspace, user_id, target_dir),
    }


@app.post("/workspace/file/delete")
async def delete_user_workspace_file(req: DeleteUserWorkspacePathRequest):
    workspace = WorkspaceManager()
    user_id = req.user_id.strip()
    deleted = _delete_user_workspace_path(workspace, user_id, req.path, expect_type="file")
    return {
        "user_id": user_id,
        "deleted": deleted,
    }


@app.post("/workspace/directory/delete")
async def delete_user_workspace_directory(req: DeleteUserWorkspacePathRequest):
    workspace = WorkspaceManager()
    user_id = req.user_id.strip()
    deleted = _delete_user_workspace_path(workspace, user_id, req.path, expect_type="directory")
    return {
        "user_id": user_id,
        "deleted": deleted,
    }


@app.post("/workspace/delete/batch")
async def batch_delete_user_workspace_paths(req: BatchDeleteUserWorkspaceRequest):
    workspace = WorkspaceManager()
    user_id = req.user_id.strip()

    if not user_id:
        raise HTTPException(status_code=400, detail="user_id is required")
    if not req.paths:
        raise HTTPException(status_code=400, detail="paths is required")

    deleted: list[dict[str, object]] = []
    failed: list[dict[str, object]] = []
    for raw_path in req.paths:
        try:
            deleted.append(_delete_user_workspace_path(workspace, user_id, raw_path))
        except HTTPException as exc:
            failed.append({
                "path": raw_path,
                "status_code": exc.status_code,
                "detail": exc.detail,
            })

    return {
        "user_id": user_id,
        "deleted": deleted,
        "failed": failed,
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


@app.post("/workspace/download/batch")
async def download_user_workspace_batch(req: BatchDownloadUserWorkspaceRequest):
    workspace = WorkspaceManager()
    user_id = req.user_id.strip()

    try:
        workspace.ensure_user_workspace(user_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    targets = _resolve_user_workspace_download_targets(workspace, user_id, req.paths)
    if len(targets) == 1 and targets[0].is_file():
        source = targets[0]
        return FileResponse(
            path=source,
            filename=source.name,
            media_type="application/octet-stream",
        )

    zip_path, download_name = _build_user_workspace_download_zip(workspace, user_id, targets)
    return FileResponse(
        path=zip_path,
        filename=download_name,
        media_type="application/zip",
    )


@app.post("/workspace/temp/copy-default-files")
async def copy_default_workspace_temp_files(req: MoveWorkspaceTempFilesRequest):
    workspace = WorkspaceManager()
    user_id = req.user_id.strip()

    if not user_id:
        raise HTTPException(status_code=400, detail="user_id is required")

    try:
        workspace.ensure_workspace()
        workspace.ensure_user_workspace(user_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    source_paths = [
        "/temp/Akcay.pdf",
        "/temp/森林每木调查数据.csv",
        "/temp/Marxist.docx",
    ]
    target_dir = _resolve_user_directory(workspace, user_id, "/temp", create=True)
    results: list[dict[str, object]] = []

    for virtual_path in source_paths:
        source = workspace.resolve_virtual_path(virtual_path)
        destination = (target_dir / source.name).resolve()
        status = "copied"

        if not source.exists():
            status = "missing"
        elif not source.is_file():
            status = "not_file"
        else:
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(source), str(destination))

        results.append({
            "source_path": virtual_path,
            "target_path": f"/temp/{source.name}",
            "filename": source.name,
            "status": status,
        })

    return {
        "user_id": user_id,
        "target_dir": "/temp",
        "items": results,
    }


@app.post("/dataspace/source/create")
async def create_dataspace_source_api(req: CreateDataspaceSourceRequest):
    try:
        source = create_dataspace_source(
            name=req.name.strip(),
            base_url=req.base_url.strip(),
            app_id=req.app_id.strip(),
            auth_code=req.auth_code.strip(),
            space_name=req.space_name.strip(),
            ftp_user=req.ftp_user.strip(),
            ftp_password=req.ftp_password,
            logo=req.logo.strip(),
        )
    except (ValueError, DataspaceError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception:
        log.exception(
            "failed to create dataspace source base_url=%s app_id=%s space_name=%s",
            req.base_url,
            req.app_id,
            req.space_name,
        )
        raise HTTPException(status_code=500, detail="failed to create dataspace source")

    return {
        "code": 200,
        "result": {
            "source": _serialize_dataspace_source(source),
        },
    }


@app.post("/dataspace/source/update")
async def update_dataspace_source_api(req: UpdateDataspaceSourceRequest):
    try:
        source = update_dataspace_source(
            source_id=req.source_id.strip(),
            name=req.name.strip(),
            base_url=req.base_url.strip(),
            app_id=req.app_id.strip(),
            auth_code=req.auth_code.strip(),
            space_name=req.space_name.strip(),
            ftp_user=req.ftp_user.strip(),
            ftp_password=req.ftp_password,
            logo=req.logo.strip(),
        )
    except (ValueError, DataspaceError) as exc:
        status_code = 404 if "dataspace source not found" in str(exc) else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc
    except Exception:
        log.exception(
            "failed to update dataspace source source_id=%s base_url=%s app_id=%s space_name=%s",
            req.source_id,
            req.base_url,
            req.app_id,
            req.space_name,
        )
        raise HTTPException(status_code=500, detail="failed to update dataspace source")

    return {
        "code": 200,
        "result": {
            "source": _serialize_dataspace_source(source),
        },
    }


@app.post("/dataspace/source/delete")
async def delete_dataspace_source_api(req: DataspaceSourceDetailRequest):
    try:
        delete_dataspace_source(req.source_id.strip())
    except DataspaceError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception:
        log.exception("failed to delete dataspace source source_id=%s", req.source_id)
        raise HTTPException(status_code=500, detail="failed to delete dataspace source")

    return {
        "code": 200,
        "result": {
            "source_id": req.source_id.strip(),
        },
    }


@app.post("/dataspace/source/list")
async def list_dataspace_sources_api():
    try:
        items = list_registered_dataspace_sources()
    except Exception:
        log.exception("failed to list dataspace sources")
        raise HTTPException(status_code=500, detail="failed to list dataspace sources")

    return {
        "code": 200,
        "result": {
            "items": [_serialize_dataspace_source_list_item(item) for item in items],
        },
    }


@app.post("/dataspace/source/detail")
async def get_dataspace_source_detail_api(req: DataspaceSourceDetailRequest):
    try:
        source = get_dataspace_source(req.source_id.strip())
    except DataspaceError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception:
        log.exception("failed to get dataspace source detail source_id=%s", req.source_id)
        raise HTTPException(status_code=500, detail="failed to get dataspace source detail")

    return {
        "code": 200,
        "result": {
            "source": _serialize_dataspace_source(source),
        },
    }


@app.post("/dataspace/source/directory/list")
async def list_dataspace_source_directory_api(req: DataspaceSourceDirectoryListRequest):
    try:
        result = list_dataspace_source_directory(
            req.source_id.strip(),
            relative_path=req.path.strip(),
        )
    except DataspaceError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception:
        log.exception(
            "failed to list dataspace source directory source_id=%s path=%s",
            req.source_id,
            req.path,
        )
        raise HTTPException(status_code=500, detail="failed to list dataspace source directory")

    return {
        "code": 200,
        "result": result,
    }


@app.post("/dataspace/source/validate")
async def validate_dataspace_source_api(req: ValidateDataspaceSourceRequest):
    try:
        result = validate_dataspace_source_connection(
            base_url=req.base_url.strip(),
            app_id=req.app_id.strip(),
            auth_code=req.auth_code.strip(),
            space_name=req.space_name.strip(),
            ftp_user=req.ftp_user.strip(),
            ftp_password=req.ftp_password,
            logo="",
        )
    except (ValueError, DataspaceError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception:
        log.exception(
            "failed to validate dataspace source base_url=%s app_id=%s space_name=%s",
            req.base_url,
            req.app_id,
            req.space_name,
        )
        raise HTTPException(status_code=500, detail="failed to validate dataspace source")

    return {
        "code": 200,
        "result": {
            "valid": True,
            "space_name": result["space_name"],
            "space_id": result["space_id"],
            "ftp_link": result["ftp_link"],
            "webdav_link": result["webdav_link"],
            "root_path": result["root_path"],
            "logo": result["logo"],
        },
    }


@app.post("/dataspace/source/validate/by-id")
async def validate_registered_dataspace_source_api(req: ValidateRegisteredDataspaceSourceRequest):
    try:
        result = validate_registered_dataspace_source(req.source_id.strip())
    except (ValueError, DataspaceError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception:
        log.exception(
            "failed to validate registered dataspace source source_id=%s",
            req.source_id,
        )
        raise HTTPException(status_code=500, detail="failed to validate registered dataspace source")

    return {
        "code": 200,
        "result": {
            "valid": True,
            "source_id": result["source_id"],
            "space_name": result["space_name"],
            "space_id": result["space_id"],
            "ftp_link": result["ftp_link"],
            "webdav_link": result["webdav_link"],
            "root_path": result["root_path"],
            "logo": result["logo"],
        },
    }


@app.post("/datasource/catalog/list")
async def list_datasource_catalog_api():
    try:
        items = list_datasource_catalog()
    except Exception:
        log.exception("failed to list datasource catalog")
        raise HTTPException(status_code=500, detail="failed to list datasource catalog")

    return {
        "code": 200,
        "result": {
            "items": items,
        },
    }


@app.post("/datasource/catalog/detail")
async def get_datasource_catalog_detail_api(req: DatasourceCatalogDetailRequest):
    try:
        item = get_datasource_catalog_detail(req.type_code)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception:
        log.exception("failed to get datasource catalog detail type_code=%s", req.type_code)
        raise HTTPException(status_code=500, detail="failed to get datasource catalog detail")

    return {
        "code": 200,
        "result": {
            "catalog": item,
        },
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


@app.get("/workspace/download/root")
async def download_workspace_root_file(path: str):
    workspace = WorkspaceManager()
    try:
        workspace.ensure_workspace()
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


@app.post("/storage/juicefs/save")
async def save_juicefs_file(req: SaveJuicefsFileRequest):
    service = ObjectStorageService()

    try:
        result = service.save_local_file_juicefs(
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
            "failed to save local file to juicefs user_id=%s target_path=%s local_path=%s",
            req.user_id,
            req.target_path,
            req.local_path,
        )
        raise HTTPException(status_code=500, detail="failed to save file to juicefs")

    return {
        "code": 200,
        "result": result,
    }


@app.post("/storage/juicefs/list")
async def list_juicefs_files(req: ListJuicefsFilesRequest):
    service = ObjectStorageService()

    try:
        result = service.list_directory_juicefs(
            user_id=req.user_id,
            dir_path=req.dir_path,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception:
        log.exception(
            "failed to list juicefs directory user_id=%s dir_path=%s",
            req.user_id,
            req.dir_path,
        )
        raise HTTPException(status_code=500, detail="failed to list juicefs directory")

    return {
        "code": 200,
        "result": result,
    }


@app.post("/storage/juicefs/mkdir")
async def create_juicefs_directory(req: CreateJuicefsDirectoryRequest):
    service = ObjectStorageService()

    try:
        result = service.mkdir_juicefs(
            user_id=req.user_id,
            dir_path=req.dir_path,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception:
        log.exception(
            "failed to create juicefs directory user_id=%s dir_path=%s",
            req.user_id,
            req.dir_path,
        )
        raise HTTPException(status_code=500, detail="failed to create juicefs directory")

    return {
        "code": 200,
        "result": result,
    }


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
