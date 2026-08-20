import logging
from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field

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


class CorpusDatasetListRequest(CorpusPageListRequest):
    model_config = ConfigDict(populate_by_name=True)

    id: str | None = None
    title: str | None = None
    titleEn: str | None = None
    field: str | None = None
    subject: str | None = None
    type: str | None = None
    corpusType: str | None = None
    keywords: str | None = None
    keywordsEn: str | None = None
    description: str | None = None
    descriptionEn: str | None = None
    usage: str | None = None
    cstr: str | None = None
    doi: str | None = None
    version: str | None = None
    fileNumber: int | None = None
    number: int | None = None
    size: str | None = None
    rawFormat: str | None = None
    publisher: str | None = None
    author: str | None = None
    temporal: str | None = None
    geographicCoverage: str | None = None
    language: str | None = None
    source: str | None = None
    cover: str | None = None
    fundingProject: str | None = None
    copyRight: str | None = None
    sharingMethods: str | None = None
    publishAt: datetime | None = None
    receiveAt: datetime | None = None
    updateAt: datetime | None = None
    pushAt: datetime | None = None
    status: int | None = None
    dataSetId: str | None = None
    connectorId: str | None = None
    from_: str | None = Field(default=None, alias="from")
    fromName: str | None = None

    def to_query_payload(self) -> dict[str, object]:
        payload = self.model_dump(exclude={"pageNum", "pageSize", "from_"}, exclude_none=True)
        if self.from_ is not None:
            payload["from"] = self.from_
        return payload


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
async def list_corpus_datasets_api(req: CorpusDatasetListRequest):
    try:
        result = list_dataset_details(
            page_num=req.pageNum,
            page_size=req.pageSize,
            filters=req.to_query_payload(),
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
