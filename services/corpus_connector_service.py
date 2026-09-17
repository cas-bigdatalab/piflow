from __future__ import annotations

import io
import json
import re
import secrets
import string
import tarfile
import time
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote, unquote, urlencode, urlparse
from uuid import uuid4

import requests
from botocore.auth import S3SigV4Auth
from botocore.awsrequest import AWSRequest
from botocore.credentials import Credentials

from infra.config_loader import get_settings

REQUEST_TIMEOUT = 30
DEFAULT_REMOTE_GRPC_PORT = 50061
_TTL_PATTERN = re.compile(r"^\s*(\d+)\s*([smhdSMHD]?)\s*$")


def create_remote_execution_client(remote_grpc_target: str):
    from piflow_engine.cn.piflow.remote.client import RemoteExecutionClient

    return RemoteExecutionClient(remote_grpc_target)


def list_connector_resources(
    *,
    page_num: int = 1,
    page_size: int = 10,
    grpc_port: int = DEFAULT_REMOTE_GRPC_PORT,
    keyword: str | None = None,
) -> dict[str, dict[str, Any]]:
    if page_num <= 0:
        raise ValueError("page_num must be positive")
    if page_size <= 0:
        raise ValueError("page_size must be positive")
    if grpc_port <= 0:
        raise ValueError("grpc_port must be positive")

    payload = _fetch_connector_page(page_num=page_num, page_size=page_size, keyword=keyword)
    items = _filter_connector_items(
        _extract_connector_page_items(payload),
        keyword=keyword,
    )

    result: dict[str, dict[str, Any]] = {}
    for item in items:
        connector = _normalize_connector_detail(item)
        connector_id = str(connector.get("connectorId", "") or "").strip()
        if not connector_id:
            continue
        remote_grpc_target, resource = _resolve_remote_resource(connector, grpc_port=grpc_port)
        result[connector_id] = {
            "connector": connector,
            "remote_grpc_target": remote_grpc_target,
            "resource": resource,
        }
    return result


def list_connector_details(
    *,
    page_num: int = 1,
    page_size: int = 10,
    keyword: str | None = None,
) -> dict[str, Any]:
    payload = _fetch_connector_page(page_num=page_num, page_size=page_size, keyword=keyword)
    items = _filter_connector_items(
        _extract_connector_page_items(payload),
        keyword=keyword,
    )

    result_items: list[dict[str, Any]] = []
    for item in items:
        connector = _normalize_connector_detail(item)
        if not str(connector.get("connectorId", "") or "").strip():
            continue
        result_items.append({"connector": connector})
    return {
        "items": result_items,
        "pagination": _extract_pagination(payload, page_num=page_num, page_size=page_size, item_count=len(result_items)),
    }


def list_connector_details_with_resources(
    *,
    page_num: int = 1,
    page_size: int = 10,
    grpc_port: int = DEFAULT_REMOTE_GRPC_PORT,
    keyword: str | None = None,
) -> dict[str, Any]:
    payload = _fetch_connector_page(page_num=page_num, page_size=page_size, keyword=keyword)
    items = _filter_connector_items(
        _extract_connector_page_items(payload),
        keyword=keyword,
    )

    result_items: list[dict[str, Any]] = []
    for item in items:
        connector = _normalize_connector_detail(item)
        connector_id = str(connector.get("connectorId", "") or "").strip()
        if not connector_id:
            continue
        remote_grpc_target, resource = _resolve_remote_resource(connector, grpc_port=grpc_port)
        result_items.append(
            {
                "connector": connector,
                "remote_grpc_target": remote_grpc_target,
                "resource": resource,
                "resource_display": _format_resource_display(resource),
            }
        )

    _mark_recommended_connector_items(result_items)
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

    dataset = _normalize_dataset_detail(_fetch_dataset_detail(normalized_dataset_id))
    connectors = dataset.get("connectors", [])
    connector_id = str(dataset.get("connectorId", "") or "").strip()
    if not connector_id and connectors:
        connector_id = str(connectors[0].get("connectorId", "") or "").strip()
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

    resolved_connectors = _resolve_dataset_connectors(connectors, connector_resources)
    return {
        "dataset": {
            "id": str(dataset.get("id", "")).strip(),
            "cstr": str(dataset.get("cstr", "")).strip(),
            "title": str(dataset.get("title", "")).strip(),
            "connectorId": connector_id,
            "fromName": str(dataset.get("fromName", "")).strip(),
            "connectors": resolved_connectors,
            "replicaCount": len(resolved_connectors),
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

    dataset_items = _fetch_all_dataset_items(page_size=page_size, filters=filters)
    connector_ids = {
        connector_id
        for item in dataset_items
        if isinstance(item, dict)
        for connector_id in _extract_dataset_connector_ids(item)
        if connector_id
    }
    connector_lookup = (
        _fetch_connector_details_with_resources_by_connector_id(connector_ids)
        if connector_ids
        else {}
    )

    grouped_dataset_details: dict[str, dict[str, Any]] = {}
    for item in dataset_items:
        dataset_detail = _normalize_dataset_detail(item)
        dataset_key = _first_non_empty_string(dataset_detail.get("id"), dataset_detail.get("cstr"))
        existing_detail = grouped_dataset_details.get(dataset_key)
        if existing_detail is not None:
            existing_detail["connectors"] = _merge_dataset_connectors(existing_detail["connectors"], dataset_detail["connectors"])
            continue
        grouped_dataset_details[dataset_key] = dataset_detail

    result_items: list[dict[str, Any]] = []
    for dataset_detail in grouped_dataset_details.values():
        connectors = _resolve_dataset_connectors(dataset_detail["connectors"], connector_lookup)
        available_connectors = [connector for connector in connectors if connector.get("status") == "可用"]
        _mark_recommended_connectors(available_connectors, connector_lookup)
        dataset_detail["connectors"] = available_connectors
        # A dataset is displayable only when at least one replica is available.
        if not available_connectors:
            continue
        if available_connectors:
            primary_connector = available_connectors[0]
            dataset_detail["connectorId"] = primary_connector["connectorId"]
            dataset_detail["fromName"] = primary_connector["fromName"]
            connector_organization = _first_non_empty_string(
                primary_connector.get("connectorOrganization"),
                primary_connector.get("name"),
            )
            dataset_detail["connectorOrganization"] = connector_organization
            dataset_detail["name"] = connector_organization
        dataset_detail["replicaCount"] = len(available_connectors)
        result_items.append(dataset_detail)

    start = (page_num - 1) * page_size
    end = start + page_size
    return {
        "items": result_items[start:end],
        "pagination": {
            "pageNum": page_num,
            "pageSize": page_size,
            "total": len(result_items),
        },
    }


def get_dataset_detail(dataset_id: str) -> dict[str, Any]:
    normalized_dataset_id = str(dataset_id or "").strip()
    if not normalized_dataset_id:
        raise ValueError("dataset_id is required")
    dataset_detail = _normalize_dataset_detail(_fetch_dataset_detail(normalized_dataset_id))
    connector_ids = {
        connector_id
        for connector_id in _extract_dataset_connector_ids(dataset_detail.get("raw", {}))
        if connector_id
    }
    connector_lookup = (
        _fetch_connector_details_with_resources_by_connector_id(connector_ids)
        if connector_ids
        else {}
    )
    connectors = _resolve_dataset_connectors(dataset_detail["connectors"], connector_lookup)
    available_connectors = [connector for connector in connectors if connector.get("status") == "可用"]
    _mark_recommended_connectors(available_connectors, connector_lookup)
    dataset_detail["connectors"] = available_connectors
    if available_connectors:
        primary_connector = available_connectors[0]
        dataset_detail["connectorId"] = primary_connector["connectorId"]
        dataset_detail["fromName"] = primary_connector["fromName"]
        connector_organization = _first_non_empty_string(
            primary_connector.get("connectorOrganization"),
            primary_connector.get("name"),
        )
        dataset_detail["connectorOrganization"] = connector_organization
        dataset_detail["name"] = connector_organization
    dataset_detail["replicaCount"] = len(available_connectors)
    return dataset_detail


def get_dataset_file_jsonl(cstr: str, *, file_name: str | None = None) -> dict[str, Any]:
    normalized_cstr = _normalize_required_text(cstr, field_name="cstr")
    download_urls = _fetch_dataset_file_urls(normalized_cstr)
    if not download_urls:
        raise ValueError(f"no dataset file url found for cstr={normalized_cstr}")

    selected_record = _select_dataset_file_record(download_urls, file_name=file_name)
    file_bytes = _download_bytes(selected_record["downloadUrl"])
    parsed_json, content_file_name = _parse_json_file(
        file_bytes,
        download_url=selected_record["downloadUrl"],
    )
    return {
        "cstr": normalized_cstr,
        "fileName": selected_record["fileName"],
        "downloadUrl": selected_record["downloadUrl"],
        "contentFileName": content_file_name,
        "json": parsed_json,
    }


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


def get_corpus_connector_latency(
    connector_id: str,
    *,
    grpc_port: int = DEFAULT_REMOTE_GRPC_PORT,
) -> dict[str, Any]:
    normalized_connector_id = _normalize_required_text(connector_id, field_name="id")
    if grpc_port <= 0:
        raise ValueError("grpc_port must be positive")

    connector_lookup = _fetch_connector_details_by_connector_id({normalized_connector_id})
    connector = connector_lookup.get(normalized_connector_id)
    if connector is None:
        raise ValueError(f"connector not found: {normalized_connector_id}")

    remote_grpc_target, resource = _resolve_remote_resource(
        connector,
        grpc_port=grpc_port,
    )
    latency_ms = resource.get("latency_ms")
    if latency_ms is None:
        raise RuntimeError(
            f"failed to probe connector latency for connector_id={normalized_connector_id}"
        )
    return {
        "connectorId": normalized_connector_id,
        "remote_grpc_target": remote_grpc_target,
        "latency_ms": latency_ms,
    }


def enable_corpus_connector(connector_id: str) -> dict[str, Any]:
    normalized_connector_id = _normalize_required_text(connector_id, field_name="id")
    return _request_corpus_route("GET", "/dataset.connector.enable", params={"id": normalized_connector_id})


def get_corpus_connector_tree() -> dict[str, Any]:
    return _request_corpus_route("GET", "/dataset.connector.tree")


def create_rustfs_temporary_credentials(
    ttl: str,
    *,
    name: str | None = None,
    description: str | None = None,
) -> dict[str, Any]:
    ttl_seconds = _parse_ttl_seconds(ttl)
    expiration = datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)
    expiration_text = expiration.isoformat(timespec="milliseconds").replace("+00:00", "Z")
    generated_access_key = _generate_rustfs_access_key()
    generated_secret_key = _generate_rustfs_secret_key()

    payload = {
        "accessKey": generated_access_key,
        "secretKey": generated_secret_key,
        "name": _normalize_optional_text(name) or f"mount-{uuid4().hex[:12]}",
        "description": _normalize_optional_text(description) or "",
        "expiration": expiration_text,
    }
    response_payload = _request_rustfs_admin(
        "PUT",
        "/rustfs/admin/v3/add-service-accounts",
        json_body=payload,
    )
    credentials_payload = response_payload.get("credentials")
    if isinstance(credentials_payload, dict):
        response_payload = credentials_payload
    access_key = _normalize_required_response_text(
        response_payload.get("accessKey"),
        field_name="accessKey",
    )
    secret_key = _normalize_required_response_text(
        response_payload.get("secretKey"),
        field_name="secretKey",
    )
    response_expiration = _normalize_required_response_text(
        response_payload.get("expiration") or response_payload.get("expiry"),
        field_name="expiration",
    )
    return {
        "credentials": {
            "accessKey": access_key,
            "secretKey": secret_key,
            "expiration": response_expiration,
        }
    }


def build_rustfs_mount_info(
    file_name: str,
    *,
    ttl: str = "3m",
) -> dict[str, Any]:
    normalized_input_file_name = _normalize_required_text(file_name, field_name="fileName")
    mount_file_name = _normalize_mount_file_name(normalized_input_file_name)
    mount_dir_name = _derive_mount_dir_name(normalized_input_file_name)
    mount_path = f"/mnt/corpus/{mount_dir_name}"
    mount_account_name = _derive_mount_account_name(normalized_input_file_name)
    credentials_result = create_rustfs_temporary_credentials(
        ttl,
        name=mount_account_name,
        description=f"temporary mount credential for {mount_file_name}",
    )
    credentials = credentials_result["credentials"]
    access_key = _normalize_required_response_text(credentials.get("accessKey"), field_name="accessKey")
    secret_key = _normalize_required_response_text(credentials.get("secretKey"), field_name="secretKey")
    expiration = _normalize_required_response_text(credentials.get("expiration"), field_name="expiration")

    install_command = "curl https://rclone.org/install.sh | sudo bash"
    mkdir_command = f"mkdir -p {mount_path}"
    mount_command = (
        "rclone --config /dev/null mount MOUNTTMP:corpus \\\n"
        f"  {mount_path} \\\n"
        f"  --include '/{mount_file_name}' \\\n"
        "  --vfs-cache-mode full \\\n"
        "  --read-only \\\n"
        "  --daemon"
    )
    script = "\n".join(
        [
            "# CentOS 安装 rclone",
            install_command,
            "",
            "export RCLONE_CONFIG_MOUNTTMP_TYPE='s3'",
            "export RCLONE_CONFIG_MOUNTTMP_PROVIDER='Other'",
            f"export RCLONE_CONFIG_MOUNTTMP_ACCESS_KEY_ID='{access_key}'",
            f"export RCLONE_CONFIG_MOUNTTMP_SECRET_ACCESS_KEY='{secret_key}'",
            "export RCLONE_CONFIG_MOUNTTMP_ENDPOINT='http://10.0.85.201:9000'",
            "export RCLONE_CONFIG_MOUNTTMP_REGION='cn-east-1'",
            "",
            "# 创建本地目录",
            mkdir_command,
            "",
            mount_command,
        ]
    )
    return {
        "fileName": mount_file_name,
        "mountDirName": mount_dir_name,
        "mountPath": mount_path,
        "ttl": ttl,
        "credentials": {
            "accessKey": access_key,
            "secretKey": secret_key,
            "expiration": expiration,
        },
        "env": {
            "RCLONE_CONFIG_MOUNTTMP_TYPE": "s3",
            "RCLONE_CONFIG_MOUNTTMP_PROVIDER": "Other",
            "RCLONE_CONFIG_MOUNTTMP_ACCESS_KEY_ID": access_key,
            "RCLONE_CONFIG_MOUNTTMP_SECRET_ACCESS_KEY": secret_key,
            "RCLONE_CONFIG_MOUNTTMP_ENDPOINT": "http://10.0.85.201:9000",
            "RCLONE_CONFIG_MOUNTTMP_REGION": "cn-east-1",
        },
        "commands": {
            "installRclone": install_command,
            "mkdir": mkdir_command,
            "mount": mount_command,
        },
        "script": script,
    }


def _fetch_dataset_detail(dataset_id: str) -> dict[str, Any]:
    base_url = str(get_settings().corpus_route.base_url or "").strip().rstrip("/")
    if not base_url:
        raise ValueError("settings.corpus_route.base_url must not be empty")

    url = f"{base_url}/dataset.queryDataset"
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

    data = payload.get("data")
    if data is None or data == {}:
        raise ValueError(f"dataset detail is empty for dataset_id={dataset_id}; check upstream catalog and detail endpoint")
    if not isinstance(data, dict):
        raise ValueError(f"dataset detail response data must be an object for dataset_id={dataset_id}")
    return data


def _request_rustfs_admin(
    method: str,
    path: str,
    *,
    json_body: dict[str, Any] | None = None,
) -> dict[str, Any]:
    settings = get_settings()
    base_url = str(settings.rustfs_admin.base_url or "").strip().rstrip("/")
    if not base_url:
        raise ValueError("settings.rustfs_admin.base_url must not be empty")

    access_key = str(settings.rustfs_admin.access_key or "").strip()
    secret_key = str(settings.rustfs_admin.secret_key or "").strip()
    if not access_key or not secret_key:
        raise ValueError("settings.rustfs_admin.access_key and secret_key must not be empty")

    service = str(settings.rustfs_admin.service or "s3").strip() or "s3"
    region = str(settings.rustfs_admin.region or "us-east-1").strip() or "us-east-1"
    session_token = str(settings.rustfs_admin.session_token or "").strip()
    timeout_seconds = int(settings.rustfs_admin.timeout_seconds or REQUEST_TIMEOUT)
    if timeout_seconds <= 0:
        raise ValueError("settings.rustfs_admin.timeout_seconds must be positive")

    url = f"{base_url}{path}"
    normalized_method = str(method or "").strip().upper()
    body_text = json.dumps(_normalize_json_body(json_body), ensure_ascii=False, separators=(",", ":"))
    headers = {
        "Content-Type": "application/json",
        "X-Amz-Content-Sha256": "UNSIGNED-PAYLOAD",
    }

    request = AWSRequest(
        method=normalized_method,
        url=url,
        data=body_text,
        headers=headers,
    )
    request.context["payload_signing_enabled"] = False
    S3SigV4Auth(
        Credentials(access_key=access_key, secret_key=secret_key, token=session_token or None),
        service,
        region,
    ).add_auth(request)

    prepared_request = request.prepare()
    try:
        response = requests.request(
            normalized_method,
            url,
            data=body_text,
            headers=dict(prepared_request.headers.items()),
            timeout=timeout_seconds,
        )
    except requests.RequestException as exc:
        raise RuntimeError(f"failed to request rustfs admin path={path}: {exc}") from exc
    if int(getattr(response, "status_code", 200) or 200) >= 400:
        raise RuntimeError(
            f"rustfs admin request failed path={path} "
            f"status={getattr(response, 'status_code', 'unknown')} "
            f"body={getattr(response, 'text', '')}"
        )

    payload = response.json()
    if not isinstance(payload, dict):
        raise ValueError(f"rustfs admin response must be a json object for path={path}")
    return payload


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


def _parse_ttl_seconds(ttl: str) -> int:
    normalized_ttl = str(ttl or "").strip()
    if not normalized_ttl:
        raise ValueError("ttl is required")

    match = _TTL_PATTERN.fullmatch(normalized_ttl)
    if match is None:
        raise ValueError("ttl must look like '30s', '5m', '1h', or '1d'")

    amount = int(match.group(1))
    if amount <= 0:
        raise ValueError("ttl must be positive")

    unit = match.group(2).lower() or "s"
    multiplier = {
        "s": 1,
        "m": 60,
        "h": 3600,
        "d": 86400,
    }[unit]
    ttl_seconds = amount * multiplier
    if ttl_seconds > 7 * 24 * 3600:
        raise ValueError("ttl must not exceed 7d")
    return ttl_seconds


def _normalize_mount_file_name(file_name: str) -> str:
    normalized = _normalize_required_text(file_name, field_name="fileName")
    if "." not in normalized:
        return f"{normalized}.tar"
    return normalized


def _derive_mount_dir_name(file_name: str) -> str:
    normalized = _normalize_required_text(file_name, field_name="fileName")
    name_without_suffix = Path(normalized).stem if "." in normalized else normalized
    return name_without_suffix.upper()


def _derive_mount_account_name(file_name: str) -> str:
    normalized = _normalize_required_text(file_name, field_name="fileName")
    sanitized = re.sub(r"[^a-z0-9]+", "-", normalized.lower()).strip("-")
    return f"mount-{sanitized or 'temp'}"


def _normalize_optional_text(value: Any) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip()
    return normalized or None


def _normalize_required_response_text(value: Any, *, field_name: str) -> str:
    normalized = _normalize_optional_text(value)
    if normalized is None:
        raise ValueError(f"rustfs admin response missing {field_name}")
    return normalized


def _generate_rustfs_access_key(length: int = 20) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def _generate_rustfs_secret_key(length: int = 40) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


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


def _fetch_all_dataset_items(
    *,
    page_size: int,
    filters: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Fetch all upstream pages so filtering can produce an accurate total."""
    all_items: list[dict[str, Any]] = []
    page_num = 1
    seen_pages: set[tuple[tuple[str, str, str, tuple[str, ...]], ...]] = set()

    while True:
        payload = _fetch_dataset_page(
            page_num=page_num,
            page_size=page_size,
            filters=filters,
        )
        page_items = _extract_page_items(payload, entity_name="dataset")
        if not page_items:
            break

        page_signature = tuple(
            (
                _first_non_empty_string(item.get("id")),
                _first_non_empty_string(item.get("cstr")),
                _first_non_empty_string(item.get("title"), item.get("name")),
                tuple(_extract_dataset_connector_ids(item)),
            )
            for item in page_items
        )
        # Protect against an upstream service repeatedly returning page 1.
        if page_signature in seen_pages:
            break
        seen_pages.add(page_signature)
        all_items.extend(page_items)

        if len(page_items) < page_size:
            break
        page_num += 1

    return all_items


def _fetch_dataset_file_urls(cstr: str) -> list[dict[str, Any]]:
    base_url = str(get_settings().corpus_route.base_url or "").strip().rstrip("/")
    if not base_url:
        raise ValueError("settings.corpus_route.base_url must not be empty")

    url = f"{base_url}/dataset.files?{urlencode({'cstr': cstr})}"
    try:
        response = requests.get(url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise RuntimeError(f"failed to fetch corpus dataset download urls for cstr={cstr}: {exc}") from exc

    payload = response.json()
    if not isinstance(payload, dict):
        raise ValueError(f"download urls response must be a json object for cstr={cstr}")
    if int(payload.get("code", 0) or 0) != 200:
        raise ValueError(f"download urls request failed for cstr={cstr}: {payload.get('message', '')}")

    data = payload.get("data") or []
    if not isinstance(data, list):
        raise ValueError(f"download urls response data must be a list for cstr={cstr}")

    records: list[dict[str, Any]] = []
    for item in data:
        download_urls: list[Any]
        if isinstance(item, str):
            # Keep compatibility with the old response format:
            # data: ["https://.../file.jsonl"].
            download_urls = [item]
        elif isinstance(item, dict):
            raw_download_urls = item.get("downloadUrls") or []
            download_urls = raw_download_urls if isinstance(raw_download_urls, list) else []
            if not download_urls:
                download_url = item.get("downloadUrl") or item.get("url")
                if not download_url and item.get("fileName"):
                    download_url = (
                        f"{base_url}/dataset.file.download/"
                        f"{quote(cstr, safe='')}/{quote(str(item['fileName']), safe='')}"
                    )
                download_urls = [download_url] if download_url else []
        else:
            download_urls = []

        for download_url in download_urls:
            if not isinstance(download_url, str):
                continue
            normalized = download_url.strip()
            if not normalized:
                continue
            file_name = Path(unquote(urlparse(normalized).path)).name
            if not file_name:
                continue
            records.append(
                {
                    "fileName": file_name,
                    "downloadUrl": normalized,
                }
            )
    return records


def _select_dataset_file_record(records: list[dict[str, Any]], *, file_name: str | None = None) -> dict[str, Any]:
    normalized_file_name = str(file_name or "").strip()
    if not normalized_file_name:
        return records[0]

    for record in records:
        if str(record.get("fileName", "")).strip() == normalized_file_name:
            return record

    raise ValueError(f"requested fileName not found: {normalized_file_name}")


def _download_bytes(download_url: str) -> bytes:
    try:
        response = requests.get(download_url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise RuntimeError(f"failed to download corpus dataset file from {download_url}: {exc}") from exc
    return response.content


def _parse_json_file(payload: bytes, *, download_url: str) -> tuple[Any, str]:
    if not payload:
        raise ValueError(f"downloaded empty corpus dataset file from {download_url}")

    direct_result = _try_parse_json_or_jsonl(payload)
    if direct_result is not None:
        return direct_result, Path(urlparse(download_url).path).name

    archive_result = _parse_json_from_archive(payload, download_url=download_url)
    if archive_result is not None:
        return archive_result

    raise ValueError(
        f"downloaded file is not valid json/jsonl and contains no readable json/jsonl member: {download_url}"
    )


def _try_parse_json_or_jsonl(payload: bytes) -> Any | None:
    try:
        text = payload.decode("utf-8").strip()
    except UnicodeDecodeError:
        return None
    if not text:
        return None

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        lines: list[Any] = []
        try:
            for line in text.splitlines():
                stripped = line.strip()
                if not stripped:
                    continue
                lines.append(json.loads(stripped))
        except json.JSONDecodeError:
            return None
        return lines or None

    return parsed


def _parse_json_from_archive(payload: bytes, *, download_url: str) -> tuple[Any, str] | None:
    archive_stream = io.BytesIO(payload)

    if zipfile.is_zipfile(archive_stream):
        with zipfile.ZipFile(archive_stream) as archive:
            members = [
                info
                for info in archive.infolist()
                if not info.is_dir() and _looks_like_json_file(info.filename)
            ]
            for member in members:
                parsed = _try_parse_json_or_jsonl(archive.read(member))
                if parsed is not None:
                    return parsed, member.filename

    archive_stream.seek(0)
    if tarfile.is_tarfile(archive_stream):
        archive_stream.seek(0)
        with tarfile.open(fileobj=archive_stream, mode="r:*") as archive:
            members = [
                member
                for member in archive.getmembers()
                if member.isfile() and _looks_like_json_file(member.name)
            ]
            for member in members:
                extracted = archive.extractfile(member)
                if extracted is None:
                    continue
                parsed = _try_parse_json_or_jsonl(extracted.read())
                if parsed is not None:
                    return parsed, member.name

    return None


def _looks_like_json_file(file_name: str) -> bool:
    suffix = Path(file_name).suffix.lower()
    return suffix in {".json", ".jsonl", ".ndjson"}


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


def _fetch_connector_page(
    *,
    page_num: int,
    page_size: int,
    keyword: str | None = None,
) -> dict[str, Any]:
    base_url = str(get_settings().corpus_route.base_url or "").strip().rstrip("/")
    if not base_url:
        raise ValueError("settings.corpus_route.base_url must not be empty")

    url = f"{base_url}/dataset.connector.page"
    try:
        response = requests.get(
            url,
            params=_normalize_query_params(
                {
                    "pageNum": page_num,
                    "pageSize": page_size,
                    "keyword": keyword,
                }
            ),
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


def _filter_connector_items(
    items: list[dict[str, Any]],
    *,
    keyword: str | None,
) -> list[dict[str, Any]]:
    normalized_keyword = str(keyword or "").strip().lower()
    if not normalized_keyword:
        return items

    matched_items: list[dict[str, Any]] = []
    for item in items:
        searchable_text = " ".join(
            str(item.get(field, "") or "")
            for field in (
                "connectorId",
                "name",
                "connectorName",
                "organization",
                "organizationName",
                "description",
                "remark",
            )
        ).lower()
        if normalized_keyword in searchable_text:
            matched_items.append(item)
    return matched_items


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
    enabled = source.get("enabled")
    service_url = _first_non_empty_string(
        source.get("serviceUrl"),
        source.get("serverUrl"),
    )
    protocol = _first_non_empty_string(
        source.get("protocol"),
    )
    institution = _first_non_empty_string(
        _extract_nested_text(source, "institution"),
        _extract_nested_text(source, "institutionName"),
        _extract_nested_text(source, "organization"),
        _extract_nested_text(source, "organizationName"),
        _extract_nested_text(source, "orgName"),
        _extract_nested_text(source, "companyName"),
        _extract_nested_text(source, "fromName"),
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
    sync = _first_non_empty_string(
        source.get("sync"),
        source.get("syncAt"),
        source.get("lastSyncAt"),
        source.get("updateAt"),
        source.get("updatedAt"),
        source.get("pushAt"),
    )
    recommended = _normalize_bool(source.get("recommended"), default=False)

    return {
        "connectorId": connector_id,
        "name": connector_name,
        "enabled": enabled,
        "serviceUrl": service_url,
        "protocol": protocol,
        "institution": institution,
        "host": host,
        "remoteGrpcTarget": remote_grpc_target,
        "grpcPort": grpc_port,
        "sync": sync,
        "recommended": recommended,
        "raw": source,
    }


def _normalize_dataset_detail(source: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(source, dict):
        raise ValueError("dataset detail must be a json object")

    connectors = _extract_dataset_connectors(source)
    primary_connector = connectors[0] if connectors else {"connectorId": "", "fromName": ""}
    return {
        "id": _first_non_empty_string(source.get("id")),
        "cstr": _first_non_empty_string(source.get("cstr")),
        "title": _first_non_empty_string(source.get("title"), source.get("name")),
        "connectorId": _first_non_empty_string(source.get("connectorId"), primary_connector.get("connectorId")),
        "fromName": _first_non_empty_string(source.get("fromName"), primary_connector.get("fromName")),
        "connectors": connectors,
        "replicaCount": len(connectors),
        "raw": source,
    }


def _extract_dataset_connector_ids(source: dict[str, Any]) -> list[str]:
    return [
        connector_id
        for connector in _extract_dataset_connectors(source)
        if (connector_id := str(connector.get("connectorId", "") or "").strip())
    ]


def _extract_dataset_connectors(source: dict[str, Any]) -> list[dict[str, str]]:
    connectors: list[dict[str, str]] = []
    seen_connector_ids: set[str] = set()

    def append_connector(candidate: Any) -> None:
        normalized = _normalize_dataset_connector_entry(candidate)
        connector_id = normalized["connectorId"]
        if not connector_id or connector_id in seen_connector_ids:
            return
        seen_connector_ids.add(connector_id)
        connectors.append(normalized)

    for key in ("fromList", "connectors", "connectorList", "replicas", "datasetCopies", "copies"):
        value = source.get(key)
        if isinstance(value, list):
            for item in value:
                append_connector(item)

    append_connector(source)
    return connectors


def _normalize_dataset_connector_entry(source: Any) -> dict[str, str]:
    if isinstance(source, str):
        return {
            "connectorId": source.strip(),
            "fromName": "",
        }
    if not isinstance(source, dict):
        return {"connectorId": "", "fromName": ""}

    nested_connector = source.get("connector")
    connector_id = _first_non_empty_string(
        source.get("connectorId"),
        source.get("from"),
        source.get("sourceId"),
        nested_connector.get("connectorId") if isinstance(nested_connector, dict) else "",
    )
    from_name = _first_non_empty_string(
        source.get("fromName"),
        source.get("name"),
        source.get("connectorName"),
        nested_connector.get("fromName") if isinstance(nested_connector, dict) else "",
        nested_connector.get("name") if isinstance(nested_connector, dict) else "",
    )
    return {
        "connectorId": connector_id,
        "fromName": from_name,
    }


def _resolve_dataset_connectors(
    connectors: list[dict[str, str]],
    connector_lookup: dict[str, dict[str, Any]],
) -> list[dict[str, str]]:
    resolved: list[dict[str, str]] = []
    for connector_ref in connectors:
        connector_id = str(connector_ref.get("connectorId", "") or "").strip()
        connector = connector_lookup.get(connector_id) if connector_id else None

        connector_name = _first_non_empty_string(
            connector_ref.get("fromName"),
            _extract_nested_text(connector, "name") if connector else "",
            _extract_nested_text(connector, "connectorName") if connector else "",
        )
        connector_organization = _extract_connector_organization(connector)
        enabled = _is_connector_enabled(connector) if connector is not None else False
        resolved_connector = {
            "connectorId": connector_id,
            "fromName": connector_name,
            "connectorOrganization": connector_organization,
            "name": connector_organization,
            "status": "可用" if enabled else "不可用",
            "sync": _first_non_empty_string(connector.get("sync")) if connector else "",
            "recommended": _normalize_bool(connector.get("recommended"), default=False) if connector else False,
        }
        resource = connector.get("resource") if connector else None
        latency_ms = resource.get("latency_ms") if isinstance(resource, dict) else None
        if latency_ms is not None:
            resolved_connector["latency_ms"] = latency_ms
        resolved.append(resolved_connector)
    return resolved


def _merge_dataset_connectors(
    left: list[dict[str, str]],
    right: list[dict[str, str]],
) -> list[dict[str, str]]:
    merged: list[dict[str, str]] = []
    seen_connector_ids: set[str] = set()
    for connector in [*left, *right]:
        connector_id = str(connector.get("connectorId", "") or "").strip()
        if not connector_id or connector_id in seen_connector_ids:
            continue
        seen_connector_ids.add(connector_id)
        merged.append(
            {
                "connectorId": connector_id,
                "fromName": str(connector.get("fromName", "") or "").strip(),
            }
        )
    return merged


def _normalize_bool(value: Any, *, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "1", "yes", "on"}:
            return True
        if normalized in {"false", "0", "no", "off"}:
            return False
    return default


def _fetch_remote_resource(remote_grpc_target: str) -> dict[str, Any]:
    client = create_remote_execution_client(remote_grpc_target)
    started_at = time.perf_counter()
    try:
        resource = client.get_server_resource()
    finally:
        client.close()
    latency_ms = round((time.perf_counter() - started_at) * 1000, 3)
    return {
        "cpu_cores": float(resource.cpu_cores),
        "memory_gb": float(resource.memory_gb),
        "free_disk_gb": float(resource.free_disk_gb),
        "hostname": str(resource.hostname),
        "latency_ms": latency_ms,
    }


def _resolve_remote_resource(connector: dict[str, Any], *, grpc_port: int) -> tuple[str, dict[str, Any]]:
    try:
        remote_grpc_target = _build_remote_grpc_target(connector, grpc_port=grpc_port)
    except ValueError:
        return "", _empty_remote_resource()

    try:
        resource = _fetch_remote_resource(remote_grpc_target)
    except Exception:
        return remote_grpc_target, _empty_remote_resource()

    return remote_grpc_target, resource


def _empty_remote_resource() -> dict[str, Any]:
    return {
        "cpu_cores": None,
        "memory_gb": None,
        "free_disk_gb": None,
        "hostname": None,
        "latency_ms": None,
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


def _fetch_connector_details_with_resources_by_connector_id(
    connector_ids: set[str],
) -> dict[str, dict[str, Any]]:
    lookup = _fetch_connector_details_by_connector_id(connector_ids)
    for connector_id, connector in lookup.items():
        remote_grpc_target, resource = _resolve_remote_resource(
            connector,
            grpc_port=DEFAULT_REMOTE_GRPC_PORT,
        )
        lookup[connector_id] = {
            **connector,
            "remote_grpc_target": remote_grpc_target,
            "resource": resource,
        }
    return lookup


def _mark_recommended_connector_items(items: list[dict[str, Any]]) -> None:
    resource_items = [
        item
        for item in items
        if _resource_is_available(item.get("resource"))
        and _is_connector_enabled(item.get("connector", {}))
    ]
    if not resource_items:
        return
    recommended_item = max(
        resource_items,
        key=lambda item: _resource_sort_key(item["resource"]),
    )
    recommended_id = str(
        recommended_item.get("connector", {}).get("connectorId", "") or ""
    ).strip()
    for item in items:
        connector = item.get("connector")
        if isinstance(connector, dict):
            connector["recommended"] = (
                str(connector.get("connectorId", "") or "").strip() == recommended_id
            )


def _mark_recommended_connectors(
    connectors: list[dict[str, Any]],
    connector_lookup: dict[str, dict[str, Any]],
) -> None:
    resource_items = [
        connector
        for connector in connectors
        if _resource_is_available(
            connector_lookup.get(str(connector.get("connectorId", "")).strip(), {}).get("resource")
        )
        and connector.get("status") == "可用"
    ]
    if not resource_items:
        return
    recommended_connector = max(
        resource_items,
        key=lambda item: _resource_sort_key(
            connector_lookup[str(item["connectorId"])]["resource"]
        ),
    )
    recommended_id = str(recommended_connector.get("connectorId", "")).strip()
    for connector in connectors:
        connector["recommended"] = (
            str(connector.get("connectorId", "")).strip() == recommended_id
        )


def _resource_is_available(resource: Any) -> bool:
    return (
        isinstance(resource, dict)
        and resource.get("cpu_cores") is not None
        and resource.get("memory_gb") is not None
        and resource.get("free_disk_gb") is not None
    )


def _resource_sort_key(resource: dict[str, Any]) -> tuple[float, float, float]:
    return (
        float(resource.get("cpu_cores") or 0.0),
        float(resource.get("memory_gb") or 0.0),
        float(resource.get("free_disk_gb") or 0.0),
    )


def _extract_connector_institution(connector: dict[str, Any] | None) -> str:
    return _extract_connector_organization(connector)


def _is_connector_enabled(connector: dict[str, Any]) -> bool:
    enabled = connector.get("enabled")
    if isinstance(enabled, bool):
        return enabled
    if isinstance(enabled, str):
        return enabled.strip().lower() not in {"false", "0", "no", "off"}
    if isinstance(enabled, (int, float)):
        return enabled != 0
    return True


def _extract_connector_organization(connector: dict[str, Any] | None) -> str:
    if not connector:
        return ""
    return _first_non_empty_string(
        _extract_nested_text(connector, "organization"),
        _extract_nested_text(connector, "organizationName"),
        _extract_nested_text(connector, "institution"),
        _extract_nested_text(connector, "institutionName"),
        _extract_nested_text(connector, "orgName"),
        _extract_nested_text(connector, "companyName"),
    )


def _extract_nested_text(source: dict[str, Any], key: str) -> str:
    if not isinstance(source, dict) or not key:
        return ""

    direct_value = source.get(key)
    if isinstance(direct_value, str):
        text = direct_value.strip()
        if text:
            return text
    elif direct_value is not None and not isinstance(direct_value, (dict, list)):
        text = str(direct_value).strip()
        if text:
            return text

    for value in source.values():
        if isinstance(value, dict):
            nested = _extract_nested_text(value, key)
            if nested:
                return nested
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    nested = _extract_nested_text(item, key)
                    if nested:
                        return nested
    return ""


def _format_resource_display(resource: dict[str, Any]) -> dict[str, Any]:
    cpu_cores = resource.get("cpu_cores")
    memory_gb = resource.get("memory_gb")
    free_disk_gb = resource.get("free_disk_gb")
    hostname = resource.get("hostname")
    if cpu_cores is None and memory_gb is None and free_disk_gb is None and hostname is None:
        return {
            "hostname": None,
            "cpu": None,
            "memory": None,
            "free_disk": None,
            "summary": "",
        }

    resolved_cpu_cores = float(cpu_cores or 0.0)
    resolved_memory_gb = float(memory_gb or 0.0)
    resolved_free_disk_gb = float(free_disk_gb or 0.0)
    resolved_hostname = str(hostname or "").strip()
    return {
        "hostname": resolved_hostname,
        "cpu": f"{resolved_cpu_cores:g} 核",
        "memory": f"{resolved_memory_gb:.2f} GB",
        "free_disk": f"{resolved_free_disk_gb:.2f} GB",
        "summary": (
            f"{resolved_hostname or 'unknown'} · CPU {resolved_cpu_cores:g} 核 · "
            f"内存 {resolved_memory_gb:.2f} GB · 剩余磁盘 {resolved_free_disk_gb:.2f} GB"
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
    # Different corpus service versions place pagination beside `data`, inside
    # a paged `data` object, or inside a `pagination` object.
    candidates: list[dict[str, Any]] = []
    for key in ("pagination", "page", "data"):
        value = payload.get(key)
        if isinstance(value, dict):
            candidates.append(value)
    candidates.append(payload)

    raw_total: Any = None
    raw_page_num: Any = None
    raw_page_size: Any = None
    for candidate in candidates:
        if raw_total is None:
            for key in ("total", "count", "totalCount", "totalElements"):
                if candidate.get(key) is not None:
                    raw_total = candidate.get(key)
                    break
        if raw_page_num is None:
            for key in ("pageNum", "page", "current", "currentPage"):
                if candidate.get(key) is not None:
                    raw_page_num = candidate.get(key)
                    break
        if raw_page_size is None:
            for key in ("pageSize", "size", "limit", "perPage"):
                if candidate.get(key) is not None:
                    raw_page_size = candidate.get(key)
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
