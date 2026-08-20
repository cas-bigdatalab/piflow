"""跨域配置加载。"""

from __future__ import annotations

import logging
import os
import threading
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any

log = logging.getLogger("flow.cross_dag.config")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = PROJECT_ROOT / "config" / "cross_dc.yaml"
# 换一套中心/维度配置（演示、联调、单测）用这个环境变量指路，不用改仓库里的正式配置
CONFIG_PATH_ENV = "CROSS_DC_CONFIG"

DEFAULT_EXPORT_DIR = "/workspace/artifacts/xdc"
DEFAULT_WAIT_TIMEOUT_SECONDS = 3600


DEFAULT_LOCATION_TERM = "数据中心"

# 配置缺省时的兜底产出算子。放在这里只是为了让缺配置的老部署行为不变；
# 正式声明在 config/cross_dc.yaml 的 sink_skills 里。
FALLBACK_SINK_SKILLS = frozenset(
    {
        "piflow_engine.cn.piflow.engine.local.file_save_stop.FileSaveStop",
        "piflow_engine.cn.piflow.engine.local.dataspace_file_sink_stop.DataspaceFileSinkStop",
        "piflow_engine.cn.piflow.engine.local.llm_file_transform_stop.LlmFileTransformStop",
    }
)


@dataclass(frozen=True)
class CenterConfig:
    center_id: str
    center_name: str
    grpc_endpoint: str
    aliases: tuple[str, ...] = ()

    def mention_terms(self) -> tuple[str, ...]:
        """判定「用户提到了这个位置」时可用的全部字面量。"""
        terms = [self.center_id, self.center_name, *self.aliases]
        return tuple(t.strip() for t in terms if t and t.strip())


@dataclass(frozen=True)
class CrossDcConfig:
    local_center_id: str
    default_center_id: str
    centers: dict[str, CenterConfig] = field(default_factory=dict)
    default_grpc_port: int = 50061
    export_dir: str = DEFAULT_EXPORT_DIR
    subdag_wait_timeout_seconds: int = DEFAULT_WAIT_TIMEOUT_SECONDS
    replica_weights: dict[str, float] = field(default_factory=dict)
    available_statuses: frozenset[str] = frozenset()
    metric_directions: dict[str, str] = field(default_factory=dict)
    requirement_facets: dict[str, dict[str, str]] = field(default_factory=dict)
    sink_skills: frozenset[str] = FALLBACK_SINK_SKILLS
    placeholder_skills: frozenset[str] = frozenset()
    llm_model: str = ""
    llm_enable_thinking: bool = False
    llm_timeout_seconds: int = 120
    llm_json_mode: bool = True
    location_term: str = DEFAULT_LOCATION_TERM

    def endpoint_of(self, center_id: str) -> str:
        center = self.centers.get(center_id)
        if center is None:
            raise KeyError(
                f"unknown center_id: {center_id}. "
                f"known centers: {sorted(self.centers) or '<empty>'}"
            )
        return center.grpc_endpoint

    def has_center(self, center_id: str) -> bool:
        return center_id in self.centers

    def facet_label(self, key: str) -> str:
        return (self.requirement_facets.get(key) or {}).get("label") or key

    def facet_mode(self, key: str) -> str:
        """未声明的维度按 match_all 处理：不能假设一个不认识的维度可以分摊覆盖。"""
        from .schema import FACET_MATCH_ALL

        return (self.requirement_facets.get(key) or {}).get("mode") or FACET_MATCH_ALL


_cache: CrossDcConfig | None = None
_lock = threading.Lock()


def load_cross_dc_config(path: str | Path | None = None) -> CrossDcConfig:
    """从 yaml 读取配置。path 为 None 时读默认路径并缓存。"""
    import yaml

    if path is not None:
        target = Path(path)
    else:
        override = os.environ.get(CONFIG_PATH_ENV, "").strip()
        target = Path(override) if override else CONFIG_PATH
    raw: dict = {}
    if target.is_file():
        raw = yaml.safe_load(target.read_text(encoding="utf-8")) or {}

    default_port = int(raw.get("default_grpc_port") or 50061)
    centers: dict[str, CenterConfig] = {}
    for item in (raw.get("sources") or raw.get("centers") or []):
        center_id = str(item.get("ip") or item.get("center_id") or "").strip()
        if not center_id:
            continue
        endpoint = str(item.get("grpc_endpoint", "") or "").strip()
        if not endpoint:
            endpoint = f"{center_id}:{item.get('grpc_port') or default_port}"
        centers[center_id] = CenterConfig(
            center_id=center_id,
            center_name=str(item.get("name") or item.get("center_name") or center_id),
            grpc_endpoint=endpoint,
            aliases=tuple(str(a) for a in (item.get("aliases") or []) if str(a).strip()),
        )

    local_center_id = str(
        raw.get("local_source_ip") or raw.get("local_center_id") or ""
    ).strip()
    if local_center_id.lower() == "auto":
        local_center_id = ""
    if not local_center_id and centers:
        local_center_id = next(iter(centers), "local")

    default_center_id = str(raw.get("default_center_id", "") or "").strip() or local_center_id
    if default_center_id.lower() == "auto":
        default_center_id = ""

    selection = raw.get("replica_selection") or {}
    replica_weights = {
        str(key): float(value)
        for key, value in (selection.get("weights") or {}).items()
    }
    available_statuses = frozenset(
        str(s).strip().upper()
        for s in (selection.get("available_statuses") or [])
        if str(s).strip()
    )
    metric_directions = {
        str(k): str(v).strip().lower()
        for k, v in (selection.get("metric_directions") or {}).items()
    }
    _warn_if_locality_outvoted(replica_weights)

    export_dir = str(raw.get("export_dir", "") or DEFAULT_EXPORT_DIR)
    _warn_if_export_dir_escapes_workspace(export_dir)

    sink_skills = frozenset(
        str(x).strip() for x in (raw.get("sink_skills") or []) if str(x).strip()
    ) or FALLBACK_SINK_SKILLS
    placeholder_skills = frozenset(
        str(x).strip() for x in (raw.get("placeholder_skills") or []) if str(x).strip()
    )

    requirement_facets: dict[str, dict[str, str]] = {}
    for key, value in (raw.get("requirement_facets") or {}).items():
        entry = value if isinstance(value, dict) else {}
        requirement_facets[str(key)] = {
            "label": str(entry.get("label", "") or key),
            "mode": str(entry.get("mode", "") or "").strip().lower(),
        }

    llm_raw = raw.get("llm") or {}

    return CrossDcConfig(
        local_center_id=local_center_id,
        default_center_id=default_center_id,
        centers=centers,
        default_grpc_port=default_port,
        export_dir=export_dir,
        subdag_wait_timeout_seconds=int(
            raw.get("subdag_wait_timeout_seconds") or DEFAULT_WAIT_TIMEOUT_SECONDS
        ),
        replica_weights=replica_weights,
        available_statuses=available_statuses,
        metric_directions=metric_directions,
        requirement_facets=requirement_facets,
        sink_skills=sink_skills,
        placeholder_skills=placeholder_skills,
        llm_model=str(llm_raw.get("model", "") or ""),
        llm_enable_thinking=bool(llm_raw.get("enable_thinking", False)),
        llm_timeout_seconds=int(llm_raw.get("timeout_seconds") or 120),
        llm_json_mode=bool(llm_raw.get("json_mode", True)),
        location_term=str(
            (raw.get("terminology") or {}).get("location_term", "") or DEFAULT_LOCATION_TERM
        ),
    )


def _warn_if_export_dir_escapes_workspace(export_dir: str) -> None:
    """导出目录必须能映射进远端工作区。

    FileSaveStop 只认 /workspace/... 和 /users/... 两种前缀，其余一律按文件系统
    绝对路径处理。写成 /artifacts/xdc 看着像工作区内的相对路径，实际会落到远端
    机器的根目录 —— 本地跑不出问题，跨域一执行才失败，而且报的是权限错误，
    很难联想到是这里配错了。
    """
    path = (export_dir or "").strip()
    if path.startswith("/workspace/") or path.startswith("/users/") or path.startswith("workspace/"):
        return
    log.warning(
        "export_dir=%s 不会被映射进远端工作区，将写到远端机器的文件系统根目录；"
        "改成 /workspace/... 开头",
        export_dir,
    )


def _warn_if_locality_outvoted(weights: dict[str, float]) -> None:
    """locality 被其余指标之和压过时告警。

    注册方新增打分指标只需改 yaml、不用改代码，这条便利也意味着有人加两个
    0.2 的指标就能悄悄把「数据就近」变成少数票 —— 后果是本地有副本也跑去
    远端取数，且全程没有任何报错。加载时喊一声，比事后从 replica_decisions
    里反推便宜得多。
    """
    locality = weights.get("locality")
    if locality is None:
        return
    others = sum(value for key, value in weights.items() if key != "locality")
    if locality > others:
        return
    log.warning(
        "config/cross_dc.yaml 的 replica_selection.weights 里 locality=%s 未超过"
        "其余指标之和 %s，资源指标可以推翻「数据就近」：本地有副本时仍可能选中"
        "远端副本，凭空产生一次跨域传输。建议把 locality 提高到大于 %s",
        locality,
        others,
        others,
    )


def get_cross_dc_config() -> CrossDcConfig:
    global _cache
    if _cache is None:
        with _lock:
            if _cache is None:
                _cache = load_cross_dc_config()
    return _cache


def resolve_cross_dc_config(
    config: CrossDcConfig | None = None,
    registry: Any = None,
) -> CrossDcConfig:
    """把注册表实时拓扑合并进策略配置。

    YAML 只负责策略和可选覆盖，注册表才是数据源清单的事实来源。这样新增、下线、
    改地址的连接器会自然进入下一次规划，不必把每个 connectorId/IP 再抄一遍到
    ``cross_dc.yaml``。显式配置仍保留，用于补充非注册表节点和别名。
    """
    resolved = config or get_cross_dc_config()
    if registry is None:
        from .registry_stub import get_registry

        registry = get_registry()

    try:
        sources = list(registry.list_sources())
    except Exception as exc:
        raise RuntimeError(
            f"数据源注册表不可用，无法构建跨域拓扑: {type(exc).__name__}: {exc}"
        ) from exc

    centers = dict(resolved.centers)
    for source in sources:
        center_id = str(getattr(source, "center_id", "") or getattr(source, "ip", "")).strip()
        if not center_id:
            continue
        configured = centers.get(center_id)
        endpoint = str(getattr(source, "grpc_endpoint", "") or "").strip()
        if not endpoint:
            endpoint = (
                configured.grpc_endpoint
                if configured and configured.grpc_endpoint
                else f"{center_id}:{resolved.default_grpc_port}"
            )
        source_aliases = tuple(
            str(value).strip()
            for value in (
                getattr(source, "source_id", ""),
                *(getattr(source, "aliases", ()) or ()),
            )
            if str(value or "").strip()
        )
        configured_aliases = configured.aliases if configured else ()
        aliases = tuple(dict.fromkeys((*configured_aliases, *source_aliases)))
        centers[center_id] = CenterConfig(
            center_id=center_id,
            center_name=(
                str(getattr(source, "name", "") or "").strip()
                or (configured.center_name if configured else center_id)
            ),
            grpc_endpoint=endpoint,
            aliases=aliases,
        )

    active_ids = [
        str(getattr(source, "center_id", "") or getattr(source, "ip", "")).strip()
        for source in sources
        if str(getattr(source, "center_id", "") or getattr(source, "ip", "")).strip()
    ]
    preferred_default = (
        resolved.default_center_id
        if resolved.default_center_id in centers
        else _best_source_id(sources) or next(iter(centers), "")
    )
    local_center_id = (
        resolved.local_center_id
        if resolved.local_center_id in centers
        else preferred_default
    )

    if active_ids and not preferred_default:
        preferred_default = active_ids[0]
    return replace(
        resolved,
        local_center_id=local_center_id,
        default_center_id=preferred_default,
        centers=centers,
    )


def _best_source_id(sources: list[Any]) -> str:
    """配置未指定默认位置时，按资源选一个稳定的默认汇聚位置。"""
    available = [
        source
        for source in sources
        if str(getattr(source, "status", "AVAILABLE") or "").upper() == "AVAILABLE"
    ]
    if not available:
        available = list(sources)

    def rank(source: Any) -> tuple[float, float, float]:
        metrics = getattr(source, "metrics", {}) or {}
        return (
            _metric(metrics, "cpu_cores"),
            _metric(metrics, "memory_gb"),
            _metric(metrics, "free_disk_gb"),
        )

    if not available:
        return ""
    selected = max(available, key=rank)
    return str(
        getattr(selected, "center_id", "") or getattr(selected, "ip", "")
    ).strip()


def _metric(metrics: dict[str, Any], name: str) -> float:
    try:
        return float(metrics.get(name, 0.0) or 0.0)
    except (TypeError, ValueError):
        return 0.0


def check_centers_against_registry(registry: Any = None) -> list[str]:
    """检查动态注册拓扑和可选静态补充，空列表表示可提交。"""
    if registry is None:
        from .registry_stub import get_registry

        registry = get_registry()

    config = get_cross_dc_config()
    try:
        source_ips = {s.ip for s in registry.list_sources() if s.ip}
    except Exception as exc:
        return [f"数据源注册表不可用，无法比对中心清单: {type(exc).__name__}: {exc}"]

    configured = set(config.centers)
    runtime = resolve_cross_dc_config(config, registry)
    problems: list[str] = []

    stale = sorted(configured - source_ips)
    if stale:
        problems.append(
            f"config 配了这些中心，但注册表里没有对应数据源：{stale}。"
            "多半是配置写早了或数据源下线了，规划器会把它们当成可选执行位置"
        )

    missing_endpoints = sorted(
        center_id
        for center_id in source_ips
        if not runtime.centers.get(center_id)
        or not runtime.centers[center_id].grpc_endpoint
    )
    if missing_endpoints:
        problems.append(f"这些注册数据源没有可用的 gRPC 地址：{missing_endpoints}")

    if not runtime.default_center_id:
        problems.append("无法从配置或注册表确定默认执行位置")

    if config.local_center_id and config.local_center_id not in runtime.centers:
        problems.append(
            f"local_source_ip={config.local_center_id} 不在 sources 清单里，"
            "且注册表也没有返回该位置"
        )

    return problems


def set_cross_dc_config(config: CrossDcConfig | None) -> None:
    """测试注入点。传 None 清空缓存。"""
    global _cache
    with _lock:
        _cache = config
