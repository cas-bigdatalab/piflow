import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.corpus_connector_service import (
    get_dataset_detail,
    list_connector_details_with_resources,
    list_dataset_details,
)

log = logging.getLogger("flow.api")
router = APIRouter()


class CorpusPageListRequest(BaseModel):
    pageNum: int = 1
    pageSize: int = 10


class CorpusDatasetDetailRequest(BaseModel):
    datasetId: str


@router.post("/corpus/connector/list")
async def list_corpus_connectors_api(req: CorpusPageListRequest):
    try:
        result = list_connector_details_with_resources(
            page_num=req.pageNum,
            page_size=req.pageSize,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception:
        log.exception(
            "failed to list corpus connectors pageNum=%s pageSize=%s",
            req.pageNum,
            req.pageSize,
        )
        raise HTTPException(status_code=500, detail="failed to list corpus connectors")

    return {
        "code": 200,
        "result": result,
    }


@router.post("/corpus/dataset/list")
async def list_corpus_datasets_api(req: CorpusPageListRequest):
    try:
        result = list_dataset_details(
            page_num=req.pageNum,
            page_size=req.pageSize,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception:
        log.exception(
            "failed to list corpus datasets pageNum=%s pageSize=%s",
            req.pageNum,
            req.pageSize,
        )
        raise HTTPException(status_code=500, detail="failed to list corpus datasets")

    return {
        "code": 200,
        "result": result,
    }


@router.post("/corpus/dataset/detail")
async def get_corpus_dataset_detail_api(req: CorpusDatasetDetailRequest):
    try:
        result = get_dataset_detail(req.datasetId)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception:
        log.exception("failed to get corpus dataset detail datasetId=%s", req.datasetId)
        raise HTTPException(status_code=500, detail="failed to get corpus dataset detail")

    return {
        "code": 200,
        "result": {
            "dataset": result,
        },
    }
