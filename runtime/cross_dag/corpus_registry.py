"""把语料寻址系统接成跨域调度的数据源注册表。

对应关系是这样定的：

    语料系统的「连接器」  ->  我们的「数据源 / 执行位置」
    语料系统的「数据集」  ->  我们的「数据集」，每个数据集可在多个所属连接器上各有一份

连接器的 serviceUrl 给出主机地址，那就是执行位置标识；资源指标通过各节点的
gRPC 现场问，用于副本打分。哪些数据集字段作为需求维度由 cross_dc.yaml 声明；
平台不认识字段语义，只做取值集合比对，所以换学科或元数据体系无需改调度代码。

失败处理的原则：单个连接器问不到资源不能拖垮整张表（那会让所有调度都不可用），
按「资源未知」记下来并降级；但连接器清单或数据集清单整体拉不到就必须抛出去，
那种情况下继续跑只会规划出一堆幻觉。
"""

from __future__ import annotations

import json
import logging
from typing import Any, Iterable
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from .registry_adapter import CallbackDatasourceRegistry
from .registry_stub import DatasetRecord, DataSourceRecord, ReplicaRecord
from .schema import BUNDLE_CORPUS_DATASET

log = logging.getLogger("flow.cross_dag.corpus_registry")

REQUEST_TIMEOUT = 30
DEFAULT_GRPC_PORT = 50061
PAGE_SIZE = 100
MAX_PAGES = 200

# 语料元数据里可以当需求维度用的字段。值里的分号是多值分隔符（"中文;英文"）。
# 想增删维度改这里和 config/cross_dc.yaml 的 requirement_facets 即可。
FACET_FIELDS = ("field", "language", "corpusType", "rawFormat")
MULTI_VALUE_SEPARATORS = (";", "；", ",", "，")
CONNECTOR_REFERENCE_KEYS = (
    "connectorId",
    "sourceId",
    "source_id",
    "centerId",
    "center_id",
    "from",
)
CONNECTOR_COLLECTION_KEYS = (
    "connectors",
    "connectorList",
    "replicas",
    "datasetCopies",
    "copies",
)


def build_corpus_registry(
    *,
    base_url: str | None = None,
    grpc_port: int = DEFAULT_GRPC_PORT,
    cache: bool = True,
    fetch_metrics: bool = True,
    facet_fields: Iterable[str] | None = None,
) -> CallbackDatasourceRegistry:
    """构造接语料系统的注册表。

    fetch_metrics=False 时跳过 gRPC 探测，只拿目录信息 —— 网络受限或只想看
    意图识别效果时用得上，副本打分会退化成只看数据本地性。
    """
    resolved_base = (base_url or _settings_base_url()).strip().rstrip("/")
    if not resolved_base:
        raise ValueError("语料系统 base_url 为空，请检查 config/app.yaml 的 corpus_route.base_url")

    resolved_facets = _resolve_facet_fields(facet_fields)
    return CallbackDatasourceRegistry(
        fetch_sources=lambda: _fetch_connectors(resolved_base),
        source_mapper=lambda raw: _map_connector(raw, grpc_port=grpc_port, probe=fetch_metrics),
        fetch_datasets=lambda: _fetch_datasets(resolved_base),
        dataset_mapper=lambda raw: _map_dataset(raw, facet_fields=resolved_facets),
        cache=cache,
    )


# ---- 拉取 ---------------------------------------------------------------

def _fetch_connectors(base_url: str) -> list[dict[str, Any]]:
    items = _paged(lambda page: _get_json(
        f"{base_url}/dataset.connector.page?pageNum={page}&pageSize={PAGE_SIZE}"))
    if not items:
        raise RuntimeError("语料系统没有返回任何连接器，跨域调度无法确定执行位置")
    return items


def _paged(fetch: Any) -> list[dict[str, Any]]:
    """按页拉全。

    终止条件用 totalPages 而不是 last —— 实测服务端在某些分页参数下 last 恒为
    False，只信它会死循环。再加一个硬上限和去重兜底：目录接口的分页行为是对方
    的实现细节，我们这边不能因为它变了就把调度卡死。
    """
    items: list[dict[str, Any]] = []
    seen: set[str] = set()
    page = 1
    while page <= MAX_PAGES:
        payload = fetch(page)
        data = payload.get("data") or {}
        if isinstance(data, list):
            content = [x for x in data if isinstance(x, dict)]
            total_pages = 1
        elif isinstance(data, dict):
            raw_content = _first_list(data, "content", "records", "list", "items")
            content = [x for x in raw_content if isinstance(x, dict)]
            total_pages = _positive_int(
                _first_value(data, "totalPages", "total_pages", "pages"),
                default=1,
            )
        else:
            break

        fresh = 0
        for item in content:
            key = (
                _first_text(item, "id", "datasetId", "dataset_id", "connectorId", "sourceId")
                or json.dumps(item, sort_keys=True)
            )
            if key in seen:
                continue
            seen.add(key)
            items.append(item)
            fresh += 1

        if page >= total_pages or fresh == 0:
            break
        page += 1
    return items


def _fetch_datasets(base_url: str) -> list[dict[str, Any]]:
    from infra.config_loader import get_settings

    # 分页参数走 query string —— 放在 POST body 里会被服务端忽略，永远只回第一页
    # 的 10 条（OpenAPI 里 pageNum/pageSize 声明的就是 in: query）。请求体是过滤
    # 条件，空对象表示不过滤。
    configured = get_settings().corpus_route.cross_dag_dataset_filters.source
    sources = list(dict.fromkeys(name.strip() for name in configured if name.strip()))
    # Keep the local configuration key; the upstream filter accepts a sources array.
    # Empty matches stay empty; a failed filtered request must not fall back to all data.
    return _paged(lambda page: _post_json(
        f"{base_url}/dataset.page?pageNum={page}&pageSize={PAGE_SIZE}",
        {"sources": sources} if sources else {}))


# ---- 映射 ---------------------------------------------------------------

def _map_connector(
    raw: dict[str, Any],
    *,
    grpc_port: int,
    probe: bool,
) -> DataSourceRecord | None:
    connector_id = _first_text(raw, "connectorId", "sourceId", "source_id", "id")
    explicit_endpoint = _first_text(
        raw, "remoteGrpcTarget", "grpcTarget", "grpc_endpoint"
    )
    host = _first_text(raw, "host", "ip") or _host_of(
        _first_text(raw, "serviceUrl", "serverUrl", "service_url")
    )
    if not host and explicit_endpoint:
        host = _host_of(explicit_endpoint)
    if not host:
        log.warning("连接器 %s 没有可用的 serviceUrl，已跳过", connector_id or "<无 id>")
        return None

    # enabled/status 任一为否都不该往上面派活
    available = _as_bool(raw.get("enabled", True), default=True) and _status_available(
        raw.get("status", 1), unknown_is_available=False
    )
    status = "AVAILABLE" if available else "DISABLED"
    grpc_endpoint = _grpc_endpoint_of(
        raw,
        host=host,
        default_port=grpc_port,
        explicit=explicit_endpoint,
    )

    metrics: dict[str, float] = {}
    if probe and available:
        metrics = _probe_metrics(grpc_endpoint)
        if not metrics:
            # 探不到资源不等于节点不可用 —— 目录里它还在，只是打分时这两维按最差算。
            # 直接标成不可用会让本来能跑的任务无处可去。
            log.warning("连接器 %s(%s) 资源探测失败，副本打分将按最差资源计", connector_id, host)

    institution = _first_text(
        raw,
        "institution",
        "institutionName",
        "organization",
        "organizationName",
        "orgName",
        "companyName",
        "fromName",
    )
    connector_name = _first_text(raw, "name", "connectorName", "sourceName")
    name = institution or connector_name or connector_id or host
    aliases = tuple(
        dict.fromkeys(
            x
            for x in (
                connector_id,
                connector_name,
                institution,
                name,
            )
            if x
        )
    )
    return DataSourceRecord(
        ip=host,
        name=name,
        status=status,
        metrics=metrics,
        aliases=aliases,
        source_id=connector_id or host,
        grpc_endpoint=grpc_endpoint,
    )


def _map_dataset(
    raw: dict[str, Any],
    *,
    facet_fields: tuple[str, ...],
) -> DatasetRecord | None:
    dataset_id = _first_text(raw, "id", "datasetId", "dataset_id")
    if not dataset_id:
        return None

    connector_ids = _connector_ids(raw)
    cstr = _first_text(raw, "cstr", "replicaId", "replica_id")
    if not connector_ids:
        log.warning("数据集 %s 没有数据源引用，已跳过", dataset_id)
        return None

    replica_base_id = cstr or dataset_id
    replicas = tuple(
        ReplicaRecord(
            replica_id=(
                replica_base_id
                if len(connector_ids) == 1
                else f"{replica_base_id}@{connector_id}"
            ),
            # 这里先保留注册中心业务 ID；CallbackDatasourceRegistry 会把每个
            # connectorId 分别规范化为实际执行位置，并合并对应节点的资源指标。
            source_ip=connector_id,
            # corpus 算子按 dataset_id 取数，所以所有物理副本共享这个 locator。
            locator=dataset_id,
            status=_replica_status(raw),
        )
        for connector_id in connector_ids
    )

    facets = _facets_of(raw, facet_fields=facet_fields)

    tags = tuple(
        dict.fromkeys(
            value
            for value in (
                *(item for values in facets.values() for item in values),
                _first_text(raw, "publisher", "publisherName"),
                *connector_ids,
            )
            if value
        )
    )

    return DatasetRecord(
        dataset_id=dataset_id,
        name=_first_text(raw, "title", "name", "datasetName") or dataset_id,
        replicas=replicas,
        description=_first_text(raw, "description", "summary")[:300],
        tags=tags,
        facets=facets,
        source_skill=BUNDLE_CORPUS_DATASET,
        source_param="dataset_id",
        source_output_param="output",
    )


def _facets_of(
    raw: dict[str, Any],
    *,
    facet_fields: Iterable[str] = FACET_FIELDS,
) -> dict[str, tuple[str, ...]]:
    facets: dict[str, tuple[str, ...]] = {}
    for key in facet_fields:
        values = _split_values(raw.get(key))
        if values:
            facets[key] = values
    return facets


def _connector_ids(value: Any) -> tuple[str, ...]:
    """Normalize one or many connector references into stable unique ids."""
    out: list[str] = []

    def append(candidate: Any) -> None:
        if isinstance(candidate, dict):
            for key in CONNECTOR_REFERENCE_KEYS:
                if key in candidate:
                    append(candidate.get(key))
            nested = candidate.get("connector")
            if isinstance(nested, dict):
                append(nested)
            for key in CONNECTOR_COLLECTION_KEYS:
                if key in candidate:
                    append(candidate.get(key))
            return
        if isinstance(candidate, (list, tuple, set)):
            for item in candidate:
                append(item)
            return

        text = _text(candidate)
        if not text:
            return
        parts = [text]
        for separator in MULTI_VALUE_SEPARATORS:
            parts = [piece for part in parts for piece in part.split(separator)]
        for part in parts:
            connector_id = part.strip()
            if connector_id and connector_id not in out:
                out.append(connector_id)

    append(value)
    return tuple(out)


def _split_values(value: Any) -> tuple[str, ...]:
    text = _text(value)
    if not text:
        return ()
    parts = [text]
    for sep in MULTI_VALUE_SEPARATORS:
        parts = [piece for part in parts for piece in part.split(sep)]
    out: list[str] = []
    for part in parts:
        cleaned = part.strip()
        if cleaned and cleaned not in out:
            out.append(cleaned)
    return tuple(out)


# ---- 辅助 ---------------------------------------------------------------


def _resolve_facet_fields(fields: Iterable[str] | None) -> tuple[str, ...]:
    if fields is None:
        try:
            from .config import get_cross_dc_config

            fields = get_cross_dc_config().requirement_facets
        except Exception:
            fields = ()
    normalized = tuple(
        dict.fromkeys(str(field).strip() for field in (fields or ()) if str(field).strip())
    )
    return normalized or FACET_FIELDS


def _grpc_endpoint_of(
    raw: dict[str, Any],
    *,
    host: str,
    default_port: int,
    explicit: str = "",
) -> str:
    if explicit:
        return explicit
    port = _positive_int(
        _first_value(raw, "grpcPort", "grpc_port"),
        default=default_port,
    )
    return f"{host}:{port}"


def _replica_status(raw: dict[str, Any]) -> str:
    if not _as_bool(raw.get("enabled", True), default=True):
        return "DISABLED"
    status = raw.get("status", "AVAILABLE")
    if isinstance(status, str):
        normalized = status.strip().upper()
        if normalized in {"0", "FALSE", "DISABLED", "OFFLINE", "DELETED"}:
            return "DISABLED"
    return "AVAILABLE" if _status_available(status, unknown_is_available=True) else "DISABLED"


def _status_available(value: Any, *, unknown_is_available: bool) -> bool:
    if value is None or value == "":
        return True
    if isinstance(value, str):
        normalized = value.strip().upper()
        if normalized in {"TRUE", "AVAILABLE", "ONLINE", "ENABLED"}:
            return True
        if normalized in {"FALSE", "DISABLED", "OFFLINE", "DELETED"}:
            return False
        try:
            return float(normalized) != 0
        except ValueError:
            # 数据集 status 往往是发布流程状态而非可用性；只有明确的禁用词才拦截。
            return unknown_is_available
    return bool(value)


def _as_bool(value: Any, *, default: bool) -> bool:
    if value is None or value == "":
        return default
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"false", "0", "no", "off", "disabled"}:
            return False
        if normalized in {"true", "1", "yes", "on", "enabled"}:
            return True
    return bool(value)


def _first_list(raw: dict[str, Any], *keys: str) -> list[Any]:
    for key in keys:
        value = raw.get(key)
        if isinstance(value, list):
            return value
    return []


def _first_value(raw: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = raw.get(key)
        if value not in (None, ""):
            return value
    return None


def _first_text(raw: dict[str, Any], *keys: str) -> str:
    return _text(_first_value(raw, *keys))


def _positive_int(value: Any, *, default: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return parsed if parsed > 0 else default


def _probe_metrics(grpc_endpoint: str) -> dict[str, float]:
    try:
        from piflow_engine.cn.piflow.remote.client import RemoteExecutionClient

        client = RemoteExecutionClient(grpc_endpoint)
        try:
            resource = client.get_server_resource()
        finally:
            client.close()
    except Exception:
        log.debug("资源探测失败 endpoint=%s", grpc_endpoint, exc_info=True)
        return {}

    return {
        "cpu_cores": float(resource.cpu_cores),
        "memory_gb": float(resource.memory_gb),
        "free_disk_gb": float(resource.free_disk_gb),
    }


def _host_of(service_url: str) -> str:
    if not service_url:
        return ""
    normalized = service_url if "://" in service_url else f"http://{service_url}"
    return _text(urlparse(normalized).hostname)


def _get_json(url: str) -> dict[str, Any]:
    with urlopen(url, timeout=REQUEST_TIMEOUT) as response:
        return _decode(response.read(), url)


def _post_json(url: str, body: dict[str, Any]) -> dict[str, Any]:
    request = Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urlopen(request, timeout=REQUEST_TIMEOUT) as response:
        return _decode(response.read(), url)


def _decode(payload: bytes, url: str) -> dict[str, Any]:
    try:
        parsed = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"语料系统返回的不是合法 JSON: {url}") from exc
    if not isinstance(parsed, dict):
        raise RuntimeError(f"语料系统返回的不是 JSON 对象: {url}")
    code = int(parsed.get("code", 0) or 0)
    if code != 200:
        raise RuntimeError(f"语料系统接口失败 {url}: code={code} message={parsed.get('message', '')}")
    return parsed


def _settings_base_url() -> str:
    from infra.config_loader import get_settings

    return str(get_settings().corpus_route.base_url or "")


def _text(value: Any) -> str:
    return str(value or "").strip()
