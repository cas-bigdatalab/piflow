import logging
import shutil
import uuid
import zipfile

from fastapi import File, Form, HTTPException, UploadFile, APIRouter
from pathlib import Path
from datetime import datetime

from pydantic import BaseModel

from runtime.chat_store import save_chat_file
from runtime.workspace_manager import WorkspaceManager
from fastapi.responses import FileResponse

router = APIRouter()
log = logging.getLogger("flow.api")

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


def resolve_user_workspace_path(
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

def _delete_user_workspace_path(
    workspace: WorkspaceManager,
    user_id: str,
    path: str,
    *,
    expect_type: str | None = None,
) -> dict[str, object]:
    target = resolve_user_workspace_path(workspace, user_id, path)

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
        target = resolve_user_workspace_path(workspace, user_id, raw_path)
        if target == user_root:
            raise HTTPException(status_code=400, detail="user workspace root path is not allowed")
        if not target.exists():
            raise HTTPException(status_code=404, detail=f"path not found: {raw_path}")
        if target in seen:
            continue
        seen.add(target)
        resolved_targets.append(target)

    return resolved_targets

def _build_user_workspace_download_zip(
    workspace: WorkspaceManager,
    user_id: str,
    targets: list[Path],
) -> tuple[Path, str]:
    workspace.ensure_workspace()
    downloads_dir = (workspace.temp / "downloads").resolve()
    downloads_dir.mkdir(parents=True, exist_ok=True)
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


@router.post("/workspace/upload")
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
        type_code="local",
        source_id="",
    )

    return {
        "file_id": record["file_id"] if record else None,
        "user_id": normalized_user_id,
        "thread_id": safe_thread_id,
        "message_id": safe_message_id,
        "path": saved_virtual_path,
        "original_filename": safe_name,
        "type_code": record["type_code"] if record else "local",
        "source_id": record["source_id"] if record else "",
        "size": len(content),
        "content_type": file.content_type,
    }


@router.post("/workspace/list")
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


@router.post("/workspace/mkdir")
async def create_user_workspace_directory(req: CreateUserWorkspaceDirectoryRequest):
    workspace = WorkspaceManager()
    user_id = req.user_id.strip()
    target_dir = resolve_user_workspace_path(workspace, user_id, req.dir_path)

    if target_dir.exists() and not target_dir.is_dir():
        raise HTTPException(status_code=400, detail="path already exists and is not a directory")

    target_dir.mkdir(parents=True, exist_ok=True)
    return {
        "user_id": user_id,
        "dir_path": _build_user_workspace_path(workspace, user_id, target_dir),
    }


@router.post("/workspace/file/delete")
async def delete_user_workspace_file(req: DeleteUserWorkspacePathRequest):
    workspace = WorkspaceManager()
    user_id = req.user_id.strip()
    deleted = _delete_user_workspace_path(workspace, user_id, req.path, expect_type="file")
    return {
        "user_id": user_id,
        "deleted": deleted,
    }


@router.post("/workspace/directory/delete")
async def delete_user_workspace_directory(req: DeleteUserWorkspacePathRequest):
    workspace = WorkspaceManager()
    user_id = req.user_id.strip()
    deleted = _delete_user_workspace_path(workspace, user_id, req.path, expect_type="directory")
    return {
        "user_id": user_id,
        "deleted": deleted,
    }


@router.post("/workspace/delete/batch")
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


@router.post("/workspace/upload/path")
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


@router.post("/workspace/download/batch")
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


@router.post("/workspace/temp/copy-default-files")
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


@router.get("/workspace/download")
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


@router.get("/workspace/download/root")
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
