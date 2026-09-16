"""FastAPI routes for chemical node operations."""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import APIRouter, HTTPException

from .service import ChemicalService

router = APIRouter(prefix="/chemical", tags=["chemical"])
_SERVICE: ChemicalService | None = None


def _resolve_config_path() -> Path:
    env_path = os.getenv("CHEMICAL_CONFIG_PATH", "").strip()
    if env_path:
        return Path(env_path).expanduser().resolve()

    package_dir = Path(__file__).resolve().parent
    default_path = package_dir / "config.yaml"
    if default_path.exists():
        return default_path
    return package_dir / "config.example.yaml"


def get_chemical_service() -> ChemicalService:
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = ChemicalService(_resolve_config_path())
    return _SERVICE


@router.get("/nodes")
async def list_nodes():
    try:
        result = [item.__dict__ for item in get_chemical_service().list_node_details()]
        return {"code": 200, "message": "success", "result": result}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/nodes/{node_name}")
async def get_node(node_name: str):
    try:
        result = get_chemical_service().get_node_detail(node_name).__dict__
        return {"code": 200, "message": "success", "result": result}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/nodes/refresh")
async def refresh_nodes():
    try:
        result = [item.__dict__ for item in get_chemical_service().refresh()]
        return {"code": 200, "message": "success", "result": result}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
