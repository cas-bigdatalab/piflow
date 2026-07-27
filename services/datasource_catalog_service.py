from __future__ import annotations

from typing import Any

from repositories.datasource_catalog_repository import (
    get_datasource_type_by_code,
    list_datasource_types,
)


def list_datasource_catalog() -> list[dict[str, Any]]:
    return [_serialize_catalog_item(record) for record in list_datasource_types()]


def get_datasource_catalog_detail(type_code: str) -> dict[str, Any]:
    normalized_type_code = type_code.strip().lower()
    if not normalized_type_code:
        raise ValueError("type_code is required")

    record = get_datasource_type_by_code(normalized_type_code)
    if not record:
        raise ValueError(f"datasource catalog not found: {type_code}")
    return _serialize_catalog_item(record)


def _serialize_catalog_item(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "type_code": str(record["type_code"]),
        "type_name": str(record["type_name"]),
        "category": str(record["category"]),
        "description": str(record.get("description", "") or ""),
        "logo": str(record.get("logo", "") or ""),
        "enabled": bool(record.get("enabled", True)),
        "sort_order": int(record.get("sort_order", 0) or 0),
        "capabilities": list(record.get("capabilities_json") or []),
        "init_fields": list(record.get("init_fields_json") or []),
        "extra_meta": dict(record.get("extra_meta_json") or {}),
        "created_at": record.get("created_at").isoformat() if record.get("created_at") else None,
        "updated_at": record.get("updated_at").isoformat() if record.get("updated_at") else None,
    }

