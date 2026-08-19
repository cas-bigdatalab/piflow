from fastapi import HTTPException, APIRouter
from pydantic import BaseModel

import logging
from services.object_storage_service import ObjectStorageService


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

log = logging.getLogger("flow.api")
router = APIRouter()

@router.post("/storage/save")
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


@router.post("/storage/list")
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


@router.post("/storage/juicefs/save")
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


@router.post("/storage/juicefs/list")
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


@router.post("/storage/juicefs/mkdir")
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
