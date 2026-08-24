import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Body, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field

from services.corpus_connector_service import (
    create_corpus_connector,
    delete_corpus_connector,
    disable_corpus_connector,
    get_dataset_detail,
    get_dataset_file_jsonl,
    get_corpus_connector_detail,
    get_corpus_connector_tree,
    enable_corpus_connector,
    update_corpus_connector,
    list_connector_details_with_resources,
    list_dataset_details,
)

log = logging.getLogger("flow.api")
router = APIRouter()


class CorpusPageListRequest(BaseModel):
    pageNum: int = 1
    pageSize: int = 10


class CorpusConnectorListRequest(CorpusPageListRequest):
    keyword: str | None = None


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
async def list_corpus_connectors_api(req: CorpusConnectorListRequest):
    try:
        result = list_connector_details_with_resources(
            page_num=req.pageNum,
            page_size=req.pageSize,
            keyword=req.keyword,
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


@router.get("/dataset/downloadDatasetFileAsJsonl/{cstr}", include_in_schema=False)
@router.get("/corpus/dataset/download-file-jsonl/{cstr}")
async def get_corpus_dataset_file_jsonl_api(cstr: str):
    try:
        result = get_dataset_file_jsonl(cstr)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception:
        log.exception("failed to get corpus dataset file jsonl cstr=%s", cstr)
        raise HTTPException(status_code=500, detail="failed to get corpus dataset file jsonl")

    return {"code": 200, "result": result}


@router.post("/corpus/connector/save")
@router.post("/dataset.connector.save", include_in_schema=False)
async def save_corpus_connector_api(payload: dict[str, Any] = Body(...)):
    try:
        result = create_corpus_connector(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception:
        log.exception("failed to save corpus connector")
        raise HTTPException(status_code=500, detail="failed to save corpus connector")
    return {"code": 200, "result": result}


@router.post("/corpus/connector/update")
@router.post("/dataset.connector.update", include_in_schema=False)
async def update_corpus_connector_api(payload: dict[str, Any] = Body(...)):
    try:
        result = update_corpus_connector(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception:
        log.exception("failed to update corpus connector")
        raise HTTPException(status_code=500, detail="failed to update corpus connector")
    return {"code": 200, "result": result}


@router.get("/corpus/connector/delete")
@router.get("/dataset.connector.delete", include_in_schema=False)
async def delete_corpus_connector_api(id: str = Query(...)):
    try:
        result = delete_corpus_connector(id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception:
        log.exception("failed to delete corpus connector id=%s", id)
        raise HTTPException(status_code=500, detail="failed to delete corpus connector")
    return {"code": 200, "result": result}


@router.get("/corpus/connector/disable")
@router.get("/dataset.connector.disable", include_in_schema=False)
async def disable_corpus_connector_api(id: str = Query(...)):
    try:
        result = disable_corpus_connector(id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception:
        log.exception("failed to disable corpus connector id=%s", id)
        raise HTTPException(status_code=500, detail="failed to disable corpus connector")
    return {"code": 200, "result": result}


@router.get("/corpus/connector/detail")
@router.get("/dataset.connector.detail", include_in_schema=False)
async def get_corpus_connector_detail_api(id: str = Query(...)):
    try:
        result = get_corpus_connector_detail(id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception:
        log.exception("failed to get corpus connector detail id=%s", id)
        raise HTTPException(status_code=500, detail="failed to get corpus connector detail")
    return {"code": 200, "result": result}


@router.get("/corpus/connector/enable")
@router.get("/dataset.connector.enable", include_in_schema=False)
async def enable_corpus_connector_api(id: str = Query(...)):
    try:
        result = enable_corpus_connector(id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception:
        log.exception("failed to enable corpus connector id=%s", id)
        raise HTTPException(status_code=500, detail="failed to enable corpus connector")
    return {"code": 200, "result": result}


@router.get("/corpus/connector/tree")
@router.get("/dataset.connector.tree", include_in_schema=False)
async def get_corpus_connector_tree_api():
    try:
        result = get_corpus_connector_tree()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception:
        log.exception("failed to get corpus connector tree")
        raise HTTPException(status_code=500, detail="failed to get corpus connector tree")
    return {"code": 200, "result": result}
