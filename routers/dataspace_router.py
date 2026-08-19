import logging

from fastapi import HTTPException, APIRouter
from pathlib import Path

from pydantic import BaseModel

from piflow_engine.cn.piflow.engine.datasource import DataspaceError, DataspaceSource
from routers.workspace_router import resolve_user_workspace_path
from runtime.workspace_manager import WorkspaceManager
from services.datasource_catalog_service import list_datasource_catalog, get_datasource_catalog_detail
from services.dataspace_source_service import create_dataspace_source, update_dataspace_source, delete_dataspace_source, \
    list_registered_dataspace_sources, get_dataspace_source, list_dataspace_source_directory, \
    validate_dataspace_source_connection, validate_registered_dataspace_source, upload_dataspace_source_file

log = logging.getLogger("flow.api")
router = APIRouter()

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


class UploadWorkspaceFileToDataspaceRequest(BaseModel):
    user_id: str
    source_id: str
    workspace_path: str
    target_dir: str = ""


class BatchUploadWorkspacePathsToDataspaceRequest(BaseModel):
    user_id: str
    source_id: str
    workspace_paths: list[str]
    target_dir: str = ""


def _serialize_dataspace_source(source: DataspaceSource) -> dict[str, object]:
    return {
        "source_id": source.source_id,
        "name": source.name,
        "base_url": source.base_url,
        "app_id": source.app_id,
        "auth_code": _mask_secret(source.auth_code),
        "space_name": source.space_name,
        "space_id": source.space_id,
        "ftp_user": source.ftp_user,
        "ftp_password": _mask_secret(source.ftp_password),
        "ftp_link": source.ftp_link,
        "webdav_link": source.webdav_link,
        "root_path": source.root_path,
        "logo": source.logo,
        "created_at": source.created_at.isoformat() if source.created_at else None,
        "updated_at": source.updated_at.isoformat() if source.updated_at else None,
    }

def _mask_secret(value: str) -> str:
    if not value:
        return ""
    if len(value) <= 6:
        return "*" * len(value)
    return f"{value[:3]}***{value[-2:]}"

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


def _iter_user_workspace_upload_files(
    workspace: WorkspaceManager,
    user_id: str,
    paths: list[str],
) -> list[tuple[Path, str]]:
    if not user_id.strip():
        raise HTTPException(status_code=400, detail="user_id is required")
    if not paths:
        raise HTTPException(status_code=400, detail="workspace_paths is required")

    user_root = workspace.get_user_root(user_id).resolve()
    files: list[tuple[Path, str]] = []
    seen: set[Path] = set()

    for raw_path in paths:
        target = resolve_user_workspace_path(workspace, user_id, raw_path)
        if not target.exists():
            raise HTTPException(status_code=404, detail=f"path not found: {raw_path}")
        if target.is_file():
            candidates = [target]
        elif target.is_dir():
            candidates = sorted(
                (item for item in target.rglob("*") if item.is_file()),
                key=lambda item: str(item).lower(),
            )
        else:
            raise HTTPException(status_code=400, detail=f"path is not a file or directory: {raw_path}")

        for file_path in candidates:
            if file_path in seen:
                continue
            seen.add(file_path)
            relative_path = file_path.relative_to(user_root).as_posix()
            files.append((file_path, relative_path))

    return files


@router.post("/dataspace/source/create")
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


@router.post("/dataspace/source/update")
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


@router.post("/dataspace/source/delete")
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


@router.post("/dataspace/source/list")
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


@router.post("/dataspace/source/detail")
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


@router.post("/dataspace/source/directory/list")
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


@router.post("/dataspace/source/validate")
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


@router.post("/dataspace/source/validate/by-id")
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


@router.post("/dataspace/source/workspace/file/upload")
async def upload_workspace_file_to_dataspace_api(req: UploadWorkspaceFileToDataspaceRequest):
    workspace = WorkspaceManager()
    user_id = req.user_id.strip()
    source_id = req.source_id.strip()
    workspace_path = req.workspace_path.strip()
    target_dir = req.target_dir.strip()

    if not user_id:
        raise HTTPException(status_code=400, detail="user_id is required")
    if not source_id:
        raise HTTPException(status_code=400, detail="source_id is required")
    if not workspace_path:
        raise HTTPException(status_code=400, detail="workspace_path is required")

    try:
        workspace.ensure_user_workspace(user_id)
        local_file = workspace.resolve_user_virtual_path(user_id, workspace_path)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if not local_file.exists():
        raise HTTPException(status_code=404, detail="workspace file not found")
    if not local_file.is_file():
        raise HTTPException(status_code=400, detail="workspace_path must be a file")

    normalized_target_dir = target_dir.strip().strip("/")
    remote_relative_path = (
        f"{normalized_target_dir}/{local_file.name}"
        if normalized_target_dir
        else local_file.name
    )

    try:
        result = upload_dataspace_source_file(
            source_id,
            relative_path=remote_relative_path,
            local_path=local_file,
        )
    except DataspaceError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception:
        log.exception(
            "failed to upload workspace file to dataspace user_id=%s source_id=%s workspace_path=%s target_dir=%s",
            user_id,
            source_id,
            workspace_path,
            target_dir,
        )
        raise HTTPException(
            status_code=500,
            detail="failed to upload workspace file to dataspace",
        )

    return {
        "code": 200,
        "result": {
            "user_id": user_id,
            "source_id": source_id,
            "workspace_path": workspace.to_user_relative_path(user_id, workspace_path),
            "target_dir": f"/{normalized_target_dir}" if normalized_target_dir else "",
            "uploaded": result,
        },
    }


@router.post("/dataspace/source/workspace/path/upload")
async def batch_upload_workspace_paths_to_dataspace_api(req: BatchUploadWorkspacePathsToDataspaceRequest):
    workspace = WorkspaceManager()
    user_id = req.user_id.strip()
    source_id = req.source_id.strip()
    target_dir = req.target_dir.strip().strip("/")

    if not user_id:
        raise HTTPException(status_code=400, detail="user_id is required")
    if not source_id:
        raise HTTPException(status_code=400, detail="source_id is required")

    try:
        workspace.ensure_user_workspace(user_id)
        upload_files = _iter_user_workspace_upload_files(workspace, user_id, req.workspace_paths)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    uploaded: list[dict[str, object]] = []
    failed: list[dict[str, object]] = []
    for local_file, workspace_relative_path in upload_files:
        remote_relative_path = (
            f"{target_dir}/{workspace_relative_path}"
            if target_dir
            else workspace_relative_path
        )
        try:
            result = upload_dataspace_source_file(
                source_id,
                relative_path=remote_relative_path,
                local_path=local_file,
            )
        except DataspaceError as exc:
            failed.append({
                "workspace_path": f"/{workspace_relative_path}",
                "target_path": f"/{remote_relative_path}",
                "detail": str(exc),
            })
        except Exception:
            log.exception(
                "failed to batch upload workspace path to dataspace user_id=%s source_id=%s workspace_path=%s target_dir=%s",
                user_id,
                source_id,
                workspace_relative_path,
                target_dir,
            )
            failed.append({
                "workspace_path": f"/{workspace_relative_path}",
                "target_path": f"/{remote_relative_path}",
                "detail": "failed to upload workspace file to dataspace",
            })
        else:
            uploaded.append({
                "workspace_path": f"/{workspace_relative_path}",
                "target_path": f"/{remote_relative_path}",
                "uploaded": result,
            })

    return {
        "code": 200,
        "result": {
            "user_id": user_id,
            "source_id": source_id,
            "target_dir": f"/{target_dir}" if target_dir else "",
            "uploaded": uploaded,
            "failed": failed,
            "total": len(upload_files),
        },
    }


@router.post("/datasource/catalog/list")
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


@router.post("/datasource/catalog/detail")
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
