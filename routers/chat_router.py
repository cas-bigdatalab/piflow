import json
import logging
import uuid
from pathlib import Path

from fastapi import HTTPException, Request, APIRouter
from pydantic import BaseModel
from starlette.responses import StreamingResponse

from piflow_engine.cn.piflow.engine.datasource import DataspaceError
from runtime.chat_store import get_user_threads, delete_thread, get_messages, get_chat_files, ensure_thread_access, \
    update_thread_time, save_message, save_chat_file
from runtime.engine import AgentEngine
from runtime.planner_engine import PlannerEngine
from runtime.workspace_manager import WorkspaceManager
from services.dataspace_source_service import check_dataspace_source_file

router = APIRouter()
log = logging.getLogger("flow.api")

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
    type_code: str = "local"
    source_id: str = ""


class AttachMessageFilesRequest(BaseModel):
    user_id: str
    thread_id: str
    message_id: int
    attachments: list[AttachmentItem]


class BindMessageDirectoryRequest(BaseModel):
    user_id: str
    thread_id: str
    message_id: int
    dir_path: str = ""
    file_path: str = ""
    recursive: bool = False

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

def _normalize_attachment_source(
    type_code: str | None,
    source_id: str | None,
) -> tuple[str, str]:
    normalized_type_code = (type_code or "local").strip().lower()
    normalized_source_id = (source_id or "").strip()

    if not normalized_type_code:
        normalized_type_code = "local"

    if normalized_type_code not in {"local", "dataspace"}:
        raise HTTPException(status_code=400, detail="unsupported attachment type_code")

    if normalized_type_code == "dataspace" and not normalized_source_id:
        raise HTTPException(status_code=400, detail="source_id is required for dataspace attachments")

    if normalized_type_code == "local":
        normalized_source_id = ""

    return normalized_type_code, normalized_source_id

def _normalize_dataspace_attachment_path(path: str) -> str:
    normalized_path = (path or "").strip().strip("/")
    if not normalized_path:
        raise HTTPException(status_code=400, detail="attachment path is required")
    if any(part in {"", ".", ".."} for part in Path(normalized_path).parts):
        raise HTTPException(status_code=400, detail="attachment path is invalid")
    return normalized_path


@router.post("/chat")
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


@router.post("/planner/chat")
async def planner_chat(req: ChatRequest, request: Request):
    engine = get_planner_engine(request)
    request_id = uuid.uuid4().hex[:8]
    result = await engine.run(
        req.message,
        req.thread_id,
        req.user_id,
        attachments=req.attachments,
        request_id=request_id,
        message_id=req.message_id,
    )
    return {"events": result}


@router.post("/planner/chat/stream")
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
                message_id=req.message_id,
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


@router.post("/chat/stream")
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
            2. 这些通过聊天接口直接上传的文件默认视为本地资源，应优先使用本地文件输入节点，例如 `source_stop`。
            3. 如果系统另外提供了附件来源元数据，则必须按来源类型选择输入节点：
               - `type_code=local` -> 使用本地文件输入节点，如 `source_stop`
               - `type_code=dataspace` -> 使用 `dataspace_file_source_stop`
            4. 如果附件形如 `dataspace://<source_id>/<relative_path>`，则必须拆解出 `source_id` 和 `relative_path`，并生成 `dataspace_file_source_stop`。
            5. 对 `dataspace://<source_id>/<relative_path>`，禁止把整串 URI 直接写入 `source_stop.file_path`，也禁止丢失 `source_id`。
            6. Workflow 中如果需要引用输入文件，请直接引用这些路径。

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


@router.post("/threads/getTitles")
async def get_threads(req: ThreadListRequest):
    threads = get_user_threads(req.user_id)
    return {"threads": threads}


@router.post("/thread/delete")
async def delete_thread_api(req: DeleteThreadRequest):
    delete_thread(req.user_id, req.thread_id)
    return {"success": True}


@router.post("/thread/messages")
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
            "type_code": row.get("type_code", "local"),
            "source_id": row.get("source_id", ""),
        })

    for message in messages:
        message["attachments"] = attachments_by_message.get(message["id"], [])

    return {"messages": messages}


@router.post("/message/create")
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

    if not ensure_thread_access(user_id, thread_id, content[:30]):
        raise HTTPException(status_code=403, detail="thread not found or access denied")
    update_thread_time(thread_id)

    message = save_message(user_id, thread_id, role, content)
    if not message:
        raise HTTPException(status_code=500, detail="failed to create message")

    return {"message": message}


@router.post("/message/attach")
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

    if not ensure_thread_access(user_id, thread_id):
        raise HTTPException(status_code=403, detail="thread not found or access denied")

    attached = []
    for item in req.attachments:
        path = item.path.strip()
        name = item.name.strip()
        type_code, source_id = _normalize_attachment_source(
            item.type_code,
            item.source_id,
        )

        if not path:
            raise HTTPException(status_code=400, detail="attachment path is required")
        if not name:
            raise HTTPException(status_code=400, detail="attachment name is required")

        if type_code == "dataspace":
            normalized_path = _normalize_dataspace_attachment_path(path)
            try:
                check_dataspace_source_file(
                    source_id,
                    relative_path=normalized_path,
                )
            except DataspaceError as exc:
                detail = str(exc)
                if "not found" in detail:
                    raise HTTPException(status_code=404, detail="attachment file not found") from exc
                raise HTTPException(status_code=400, detail=detail) from exc
            saved_path = normalized_path
        else:
            try:
                source = workspace.resolve_user_virtual_path(user_id, path)
            except ValueError as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc

            if not source.exists() or not source.is_file():
                log.info(f"attachment path {source.resolve()} is not a file")
                raise HTTPException(status_code=404, detail="attachment file not found")
            saved_path = workspace.to_user_relative_path(user_id, path)

        record = save_chat_file(
            user_id=user_id,
            thread_id=thread_id,
            message_id=message_id,
            virtual_path=saved_path,
            original_filename=name,
            type_code=type_code,
            source_id=source_id,
        )
        if record:
            attached.append({
                "file_id": record.get("file_id"),
                "path": record.get("virtual_path"),
                "name": record.get("original_filename"),
                "type_code": record.get("type_code", "local"),
                "source_id": record.get("source_id", ""),
            })

    return {"attachments": attached}


@router.post("/message/bind-directory")
async def bind_message_directory_api(req: BindMessageDirectoryRequest):
    user_id = req.user_id.strip()
    thread_id = req.thread_id.strip()
    message_id = str(req.message_id).strip()
    dir_path = req.dir_path.strip()
    file_path = req.file_path.strip()

    if not user_id:
        raise HTTPException(status_code=400, detail="user_id is required")
    if not thread_id:
        raise HTTPException(status_code=400, detail="thread_id is required")
    if not message_id:
        raise HTTPException(status_code=400, detail="message_id is required")
    if not dir_path and not file_path:
        raise HTTPException(status_code=400, detail="dir_path or file_path is required")

    workspace = WorkspaceManager()
    try:
        workspace.ensure_user_workspace(user_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if not ensure_thread_access(user_id, thread_id):
        raise HTTPException(status_code=403, detail="thread not found or access denied")

    target_path = file_path or dir_path
    try:
        source_path = workspace.resolve_user_virtual_path(user_id, target_path)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if not source_path.exists():
        raise HTTPException(status_code=404, detail="path not found")

    if source_path.is_file():
        files = [source_path]
        source_dir = source_path.parent
        bound_path = workspace.to_user_relative_path(user_id, target_path)
    elif source_path.is_dir():
        source_dir = source_path
        iterator = source_dir.rglob("*") if req.recursive else source_dir.iterdir()
        files = sorted((path for path in iterator if path.is_file()), key=lambda path: str(path).lower())
        bound_path = workspace.to_user_relative_path(user_id, target_path)
    else:
        raise HTTPException(status_code=400, detail="path must be a file or directory")

    attached = []
    for file_path in files:
        virtual_path = "/" + "/".join(file_path.relative_to(workspace.get_user_root(user_id).resolve()).parts)
        display_name = (
            file_path.name
            if source_path.is_file()
            else (
                file_path.relative_to(source_dir).as_posix()
                if req.recursive
                else file_path.name
            )
        )
        record = save_chat_file(
            user_id=user_id,
            thread_id=thread_id,
            message_id=message_id,
            virtual_path=virtual_path,
            original_filename=display_name,
            type_code="local",
            source_id="",
        )
        if record:
            attached.append({
                "file_id": record.get("file_id"),
                "path": record.get("virtual_path"),
                "name": record.get("original_filename"),
                "type_code": record.get("type_code", "local"),
                "source_id": record.get("source_id", ""),
            })

    return {
        "dir_path": bound_path if source_path.is_dir() else "",
        "file_path": bound_path if source_path.is_file() else "",
        "attachments": attached,
    }
