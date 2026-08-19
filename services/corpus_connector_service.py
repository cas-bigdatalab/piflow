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
    data = payload.get("data")
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    if isinstance(data, dict):
        for key in ("content", "records", "list", "items"):
            value = data.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
    raise ValueError("connector page response data does not contain a connector list")


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
        "host": host,
        "remoteGrpcTarget": remote_grpc_target,
        "grpcPort": grpc_port,
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


def _first_non_empty_string(*values: Any) -> str:
    for value in values:
        text = str(value or "").strip()
        if text:
            return text
    return ""
