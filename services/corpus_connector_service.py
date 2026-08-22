from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

import requests

from infra.config_loader import get_settings

REQUEST_TIMEOUT = 30
DEFAULT_REMOTE_GRPC_PORT = 50061


def create_remote_execution_client(remote_grpc_target: str):
    from piflow_engine.cn.piflow.remote.client import RemoteExecutionClient

    return RemoteExecutionClient(remote_grpc_target)


def list_connector_resources(
    *,
    page_num: int = 1,
    page_size: int = 10,
    grpc_port: int = DEFAULT_REMOTE_GRPC_PORT,
) -> dict[str, dict[str, Any]]:
    if page_num <= 0:
        raise ValueError("page_num must be positive")
    if page_size <= 0:
        raise ValueError("page_size must be positive")
    if grpc_port <= 0:
        raise ValueError("grpc_port must be positive")

    payload = _fetch_connector_page(page_num=page_num, page_size=page_size)
    items = _extract_connector_page_items(payload)

    result: dict[str, dict[str, Any]] = {}
    for item in items:
        connector = _normalize_connector_detail(item)
        connector_id = str(connector.get("connectorId", "") or "").strip()
        if not connector_id:
            continue
        remote_grpc_target = _build_remote_grpc_target(connector, grpc_port=grpc_port)
        resource = _fetch_remote_resource(remote_grpc_target)
        result[connector_id] = {
            "connector": connector,
            "remote_grpc_target": remote_grpc_target,
            "resource": resource,
        }
    return result


def list_connector_details_with_resources(
    *,
    page_num: int = 1,
    page_size: int = 10,
    grpc_port: int = DEFAULT_REMOTE_GRPC_PORT,
) -> dict[str, Any]:
    payload = _fetch_connector_page(page_num=page_num, page_size=page_size)
    items = _extract_connector_page_items(payload)

    result_items: list[dict[str, Any]] = []
    for item in items:
        connector = _normalize_connector_detail(item)
        connector_id = str(connector.get("connectorId", "") or "").strip()
        if not connector_id:
            continue
        remote_grpc_target = _build_remote_grpc_target(connector, grpc_port=grpc_port)
        resource = _fetch_remote_resource(remote_grpc_target)
        result_items.append(
            {
                "connector": connector,
                "remote_grpc_target": remote_grpc_target,
                "resource": resource,
                "resource_display": _format_resource_display(resource),
            }
        )

    return {
        "items": result_items,
        "pagination": _extract_pagination(payload, page_num=page_num, page_size=page_size, item_count=len(result_items)),
    }


def get_dataset_connector_resource(
    dataset_id: str,
    *,
    grpc_port: int = DEFAULT_REMOTE_GRPC_PORT,
) -> dict[str, Any]:
    return get_dataset_connector_detail_with_resource(dataset_id, grpc_port=grpc_port)


def get_dataset_connector_detail_with_resource(
    dataset_id: str,
    *,
    grpc_port: int = DEFAULT_REMOTE_GRPC_PORT,
    page_num: int = 1,
    page_size: int = 10,
) -> dict[str, Any]:
    normalized_dataset_id = str(dataset_id or "").strip()
    if not normalized_dataset_id:
        raise ValueError("dataset_id is required")
    if grpc_port <= 0:
        raise ValueError("grpc_port must be positive")

    dataset = _fetch_dataset_detail(normalized_dataset_id)
    connector_id = str(dataset.get("connectorId", "") or "").strip()
    if not connector_id:
        raise ValueError(f"dataset detail does not contain connectorId for dataset_id={normalized_dataset_id}")

    connector_resources = list_connector_resources(
        page_num=page_num,
        page_size=page_size,
        grpc_port=grpc_port,
    )
    connector_entry = connector_resources.get(connector_id)
    if connector_entry is None:
        raise ValueError(
            f"connector detail not found in connector page for dataset_id={normalized_dataset_id}, connectorId={connector_id}"
        )

    return {
        "dataset": {
            "id": str(dataset.get("id", "")).strip(),
            "cstr": str(dataset.get("cstr", "")).strip(),
            "title": str(dataset.get("title", "")).strip(),
            "connectorId": connector_id,
            "fromName": str(dataset.get("fromName", "")).strip(),
        },
        "connector": connector_entry["connector"],
        "remote_grpc_target": str(connector_entry["remote_grpc_target"]),
        "resource": dict(connector_entry["resource"]),
    }


def list_dataset_details(
    *,
    page_num: int = 1,
    page_size: int = 10,
    filters: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if page_num <= 0:
        raise ValueError("page_num must be positive")
    if page_size <= 0:
        raise ValueError("page_size must be positive")

    payload = _fetch_dataset_page(page_num=page_num, page_size=page_size, filters=filters)
    dataset_items = _extract_page_items(payload, entity_name="dataset")
    connector_ids = {
        str(item.get("connectorId", "") or "").strip()
        for item in dataset_items
        if isinstance(item, dict) and str(item.get("connectorId", "") or "").strip()
    }
    connector_lookup = _fetch_connector_details_by_connector_id(connector_ids) if connector_ids else {}

    result_items: list[dict[str, Any]] = []
    for item in dataset_items:
        dataset_detail = _normalize_dataset_detail(item)
        connector_id = dataset_detail["connectorId"]
        if connector_id:
            dataset_detail["connectorInstitution"] = _extract_connector_institution(
                connector_lookup.get(connector_id)
            )
        result_items.append(dataset_detail)

    return {
        "items": result_items,
        "pagination": _extract_pagination(payload, page_num=page_num, page_size=page_size, item_count=len(result_items)),
    }


def get_dataset_detail(dataset_id: str) -> dict[str, Any]:
    normalized_dataset_id = str(dataset_id or "").strip()
    if not normalized_dataset_id:
        raise ValueError("dataset_id is required")
    return _normalize_dataset_detail(_fetch_dataset_detail(normalized_dataset_id))


def create_corpus_connector(connector: dict[str, Any]) -> dict[str, Any]:
    return _request_corpus_route("POST", "/dataset.connector.save", json_body=connector)


def update_corpus_connector(connector: dict[str, Any]) -> dict[str, Any]:
    return _request_corpus_route("POST", "/dataset.connector.update", json_body=connector)


def delete_corpus_connector(connector_id: str) -> dict[str, Any]:
    normalized_connector_id = _normalize_required_text(connector_id, field_name="id")
    return _request_corpus_route("GET", "/dataset.connector.delete", params={"id": normalized_connector_id})


def disable_corpus_connector(connector_id: str) -> dict[str, Any]:
    normalized_connector_id = _normalize_required_text(connector_id, field_name="id")
    return _request_corpus_route("GET", "/dataset.connector.disable", params={"id": normalized_connector_id})


def get_corpus_connector_detail(connector_id: str) -> dict[str, Any]:
    normalized_connector_id = _normalize_required_text(connector_id, field_name="id")
    return _request_corpus_route("GET", "/dataset.connector.detail", params={"id": normalized_connector_id})


def enable_corpus_connector(connector_id: str) -> dict[str, Any]:
    normalized_connector_id = _normalize_required_text(connector_id, field_name="id")
    return _request_corpus_route("GET", "/dataset.connector.enable", params={"id": normalized_connector_id})


def get_corpus_connector_tree() -> dict[str, Any]:
    return _request_corpus_route("GET", "/dataset.connector.tree")


def _fetch_dataset_detail(dataset_id: str) -> dict[str, Any]:
    base_url = str(get_settings().corpus_route.base_url or "").strip().rstrip("/")
    if not base_url:
        raise ValueError("settings.corpus_route.base_url must not be empty")

    url = f"{base_url}/dataset/queryDataset"
    try:
        response = requests.get(
            url,
            params={"id": dataset_id},
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise RuntimeError(f"failed to fetch dataset detail for dataset_id={dataset_id}: {exc}") from exc

    payload = response.json()
    if not isinstance(payload, dict):
        raise ValueError(f"dataset detail response must be a json object for dataset_id={dataset_id}")
    if int(payload.get("code", 0) or 0) != 200:
        raise ValueError(
            f"dataset detail request failed for dataset_id={dataset_id}: {payload.get('message', '')}"
        )

    data = payload.get("data") or {}
    if not isinstance(data, dict):
        raise ValueError(f"dataset detail response data must be an object for dataset_id={dataset_id}")
    return data


def _request_corpus_route(
    method: str,
    path: str,
    *,
    params: dict[str, Any] | None = None,
    json_body: dict[str, Any] | None = None,
) -> dict[str, Any]:
    base_url = str(get_settings().corpus_route.base_url or "").strip().rstrip("/")
    if not base_url:
        raise ValueError("settings.corpus_route.base_url must not be empty")

    normalized_method = str(method or "").strip().upper()
    if normalized_method not in {"GET", "POST"}:
        raise ValueError(f"unsupported corpus route method: {method}")

    url = f"{base_url}{path}"
    normalized_params = _normalize_query_params(params)
    normalized_json_body = _normalize_json_body(json_body)
    try:
        if normalized_method == "GET":
            response = requests.get(
                url,
                params=normalized_params,
                timeout=REQUEST_TIMEOUT,
            )
        else:
            response = requests.post(
                url,
                params=normalized_params,
                json=normalized_json_body,
                timeout=REQUEST_TIMEOUT,
            )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise RuntimeError(f"failed to request corpus route path={path}: {exc}") from exc

    payload = response.json()
    if not isinstance(payload, dict):
        raise ValueError(f"corpus route response must be a json object for path={path}")
    return payload


def _fetch_dataset_page(*, page_num: int, page_size: int, filters: dict[str, Any] | None = None) -> dict[str, Any]:
    base_url = str(get_settings().corpus_route.base_url or "").strip().rstrip("/")
    if not base_url:
        raise ValueError("settings.corpus_route.base_url must not be empty")

    url = f"{base_url}/dataset/page"
    request_body = _normalize_dataset_filters(filters)
    try:
        response = requests.post(
            url,
            params={"pageNum": page_num, "pageSize": page_size},
            json=request_body,
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise RuntimeError(
            f"failed to fetch dataset page for pageNum={page_num}, pageSize={page_size}: {exc}"
        ) from exc

    payload = response.json()
    if not isinstance(payload, dict):
        raise ValueError("dataset page response must be a json object")
    if int(payload.get("code", 0) or 0) != 200:
        raise ValueError(f"dataset page request failed: {payload.get('message', '')}")
    return payload


def _normalize_dataset_filters(filters: dict[str, Any] | None) -> dict[str, Any]:
    if not filters:
        return {}

    normalized: dict[str, Any] = {}
    for key, value in filters.items():
        if value is None:
            continue
        if isinstance(value, str):
            text = value.strip()
            if text:
                normalized[key] = text
            continue
        if hasattr(value, "isoformat"):
            normalized[key] = value.isoformat()
            continue
        normalized[key] = value
    return normalized


def _normalize_query_params(params: dict[str, Any] | None) -> dict[str, Any] | None:
    if not params:
        return None

    normalized: dict[str, Any] = {}
    for key, value in params.items():
        if value is None:
            continue
        if isinstance(value, str):
            text = value.strip()
            if text:
                normalized[key] = text
            continue
        normalized[key] = value
    return normalized or None


def _normalize_json_body(payload: dict[str, Any] | None) -> dict[str, Any]:
    if not payload:
        return {}

    normalized: dict[str, Any] = {}
    for key, value in payload.items():
        if value is None:
            continue
        if isinstance(value, str):
            normalized[key] = value.strip()
            continue
        normalized[key] = value
    return normalized


def _fetch_connector_page(*, page_num: int, page_size: int) -> dict[str, Any]:
    base_url = str(get_settings().corpus_route.base_url or "").strip().rstrip("/")
    if not base_url:
        raise ValueError("settings.corpus_route.base_url must not be empty")

    url = f"{base_url}/dataset.connector.page"
    try:
        response = requests.get(
            url,
            params={"pageNum": page_num, "pageSize": page_size},
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise RuntimeError(
            f"failed to fetch connector page for pageNum={page_num}, pageSize={page_size}: {exc}"
        ) from exc

    payload = response.json()
    if not isinstance(payload, dict):
        raise ValueError("connector page response must be a json object")
    if int(payload.get("code", 0) or 0) != 200:
        raise ValueError(f"connector page request failed: {payload.get('message', '')}")
    return payload


def _extract_connector_page_items(payload: dict[str, Any]) -> list[dict[str, Any]]:
    return _extract_page_items(payload, entity_name="connector")


def _normalize_connector_detail(source: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(source, dict):
        raise ValueError("connector detail must be a json object")

    connector_id = _first_non_empty_string(
        source.get("connectorId"),
    )
    connector_name = _first_non_empty_string(
        source.get("name"),
        source.get("connectorName"),
    )
    service_url = _first_non_empty_string(
        source.get("serviceUrl"),
        source.get("serverUrl"),
    )
    protocol = _first_non_empty_string(
        source.get("protocol"),
    )
    institution = _first_non_empty_string(
        source.get("institution"),
        source.get("institutionName"),
        source.get("organization"),
        source.get("organizationName"),
        source.get("orgName"),
        source.get("companyName"),
        source.get("fromName"),
    )
    host = _first_non_empty_string(
        source.get("host"),
        source.get("ip"),
    )
    remote_grpc_target = _first_non_empty_string(
        source.get("remoteGrpcTarget"),
        source.get("grpcTarget"),
    )
    grpc_port = _first_non_empty_string(
        source.get("grpcPort"),
    )

    return {
        "connectorId": connector_id,
        "name": connector_name,
        "serviceUrl": service_url,
        "protocol": protocol,
        "institution": institution,
        "host": host,
        "remoteGrpcTarget": remote_grpc_target,
        "grpcPort": grpc_port,
        "raw": source,
    }


def _normalize_dataset_detail(source: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(source, dict):
        raise ValueError("dataset detail must be a json object")

    return {
        "id": _first_non_empty_string(source.get("id")),
        "cstr": _first_non_empty_string(source.get("cstr")),
        "title": _first_non_empty_string(source.get("title"), source.get("name")),
        "connectorId": _first_non_empty_string(source.get("connectorId")),
        "fromName": _first_non_empty_string(source.get("fromName")),
        "raw": source,
    }


def _fetch_remote_resource(remote_grpc_target: str) -> dict[str, Any]:
    client = create_remote_execution_client(remote_grpc_target)
    try:
        resource = client.get_server_resource()
    finally:
        client.close()
    return {
        "cpu_cores": float(resource.cpu_cores),
        "memory_gb": float(resource.memory_gb),
        "free_disk_gb": float(resource.free_disk_gb),
        "hostname": str(resource.hostname),
    }


def _fetch_connector_details_by_connector_id(connector_ids: set[str]) -> dict[str, dict[str, Any]]:
    remaining_ids = {str(connector_id).strip() for connector_id in connector_ids if str(connector_id).strip()}
    if not remaining_ids:
        return {}

    lookup: dict[str, dict[str, Any]] = {}
    page_num = 1
    page_size = 100

    while remaining_ids:
        payload = _fetch_connector_page(page_num=page_num, page_size=page_size)
        items = _extract_connector_page_items(payload)
        for item in items:
            connector = _normalize_connector_detail(item)
            connector_id = connector.get("connectorId", "")
            if connector_id and connector_id in remaining_ids:
                lookup[connector_id] = connector
                remaining_ids.remove(connector_id)

        if len(items) < page_size:
            break
        page_num += 1

    return lookup


def _extract_connector_institution(connector: dict[str, Any] | None) -> str:
    if not connector:
        return ""
    return str(connector.get("institution", "") or "").strip()


def _format_resource_display(resource: dict[str, Any]) -> dict[str, Any]:
    cpu_cores = float(resource.get("cpu_cores", 0.0) or 0.0)
    memory_gb = float(resource.get("memory_gb", 0.0) or 0.0)
    free_disk_gb = float(resource.get("free_disk_gb", 0.0) or 0.0)
    hostname = str(resource.get("hostname", "") or "").strip()
    return {
        "hostname": hostname,
        "cpu": f"{cpu_cores:g} 核",
        "memory": f"{memory_gb:.2f} GB",
        "free_disk": f"{free_disk_gb:.2f} GB",
        "summary": (
            f"{hostname or 'unknown'} · CPU {cpu_cores:g} 核 · "
            f"内存 {memory_gb:.2f} GB · 剩余磁盘 {free_disk_gb:.2f} GB"
        ),
    }


def _build_remote_grpc_target(connector: dict[str, Any], *, grpc_port: int) -> str:
    explicit_target = str(connector.get("remoteGrpcTarget", "") or "").strip()
    if explicit_target:
        return explicit_target

    host = str(connector.get("host", "") or "").strip()
    if not host:
        service_url = str(connector.get("serviceUrl", "") or "").strip()
        host = _extract_host(service_url)
    if not host:
        connector_id = str(connector.get("connectorId", "") or "").strip()
        raise ValueError(
            f"connector detail for connectorId={connector_id or '<unknown>'} does not contain host/serviceUrl/remoteGrpcTarget"
        )

    raw_grpc_port = str(connector.get("grpcPort", "") or "").strip()
    resolved_port = grpc_port
    if raw_grpc_port:
        try:
            resolved_port = int(raw_grpc_port)
        except ValueError as exc:
            raise ValueError(f"invalid grpcPort in connector detail: {raw_grpc_port}") from exc
        if resolved_port <= 0:
            raise ValueError(f"invalid grpcPort in connector detail: {raw_grpc_port}")

    return f"{host}:{resolved_port}"


def _extract_host(service_url: str) -> str:
    normalized = str(service_url or "").strip()
    if not normalized:
        return ""
    if "://" not in normalized:
        normalized = f"http://{normalized}"
    parsed = urlparse(normalized)
    return str(parsed.hostname or "").strip()


def _extract_page_items(payload: dict[str, Any], *, entity_name: str) -> list[dict[str, Any]]:
    data = payload.get("data")
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    if isinstance(data, dict):
        for key in ("content", "records", "list", "items", "rows", "data"):
            value = data.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
    raise ValueError(f"{entity_name} page response data does not contain a {entity_name} list")


def _extract_pagination(
    payload: dict[str, Any],
    *,
    page_num: int,
    page_size: int,
    item_count: int,
) -> dict[str, int]:
    data = payload.get("data")
    raw_total: Any = None
    raw_page_num: Any = None
    raw_page_size: Any = None

    if isinstance(data, dict):
        for key in ("total", "count", "totalCount"):
            if data.get(key) is not None:
                raw_total = data.get(key)
                break
        for key in ("pageNum", "page", "current"):
            if data.get(key) is not None:
                raw_page_num = data.get(key)
                break
        for key in ("pageSize", "size", "limit"):
            if data.get(key) is not None:
                raw_page_size = data.get(key)
                break

    total = _safe_positive_int(raw_total, default=item_count, allow_zero=True)
    resolved_page_num = _safe_positive_int(raw_page_num, default=page_num)
    resolved_page_size = _safe_positive_int(raw_page_size, default=page_size)

    return {
        "pageNum": resolved_page_num,
        "pageSize": resolved_page_size,
        "total": total,
    }


def _safe_positive_int(value: Any, *, default: int, allow_zero: bool = False) -> int:
    try:
        resolved = int(value)
    except (TypeError, ValueError):
        return default
    if allow_zero and resolved == 0:
        return 0
    if resolved <= 0:
        return default
    return resolved


def _first_non_empty_string(*values: Any) -> str:
    for value in values:
        text = str(value or "").strip()
        if text:
            return text
    return ""


def _normalize_required_text(value: Any, *, field_name: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{field_name} is required")
    return text
