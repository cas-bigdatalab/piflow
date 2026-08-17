"""跨域配置加载。"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = PROJECT_ROOT / "config" / "cross_dc.yaml"

DEFAULT_EXPORT_DIR = "/artifacts/xdc"
DEFAULT_WAIT_TIMEOUT_SECONDS = 3600


DEFAULT_LOCATION_TERM = "数据中心"


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
    export_dir: str = DEFAULT_EXPORT_DIR
    subdag_wait_timeout_seconds: int = DEFAULT_WAIT_TIMEOUT_SECONDS
    replica_weights: dict[str, float] = field(default_factory=dict)
    available_statuses: frozenset[str] = frozenset()
    metric_directions: dict[str, str] = field(default_factory=dict)
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


_cache: CrossDcConfig | None = None
_lock = threading.Lock()


def load_cross_dc_config(path: str | Path | None = None) -> CrossDcConfig:
    """从 yaml 读取配置。path 为 None 时读默认路径并缓存。"""
    import yaml

    target = Path(path) if path is not None else CONFIG_PATH
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
    if not local_center_id:
        local_center_id = next(iter(centers), "local")

    default_center_id = str(raw.get("default_center_id", "") or "").strip() or local_center_id

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

    llm_raw = raw.get("llm") or {}

    return CrossDcConfig(
        local_center_id=local_center_id,
        default_center_id=default_center_id,
        centers=centers,
        export_dir=str(raw.get("export_dir", "") or DEFAULT_EXPORT_DIR),
        subdag_wait_timeout_seconds=int(
            raw.get("subdag_wait_timeout_seconds") or DEFAULT_WAIT_TIMEOUT_SECONDS
        ),
        replica_weights=replica_weights,
        available_statuses=available_statuses,
        metric_directions=metric_directions,
        llm_model=str(llm_raw.get("model", "") or ""),
        llm_enable_thinking=bool(llm_raw.get("enable_thinking", False)),
        llm_timeout_seconds=int(llm_raw.get("timeout_seconds") or 120),
        llm_json_mode=bool(llm_raw.get("json_mode", True)),
        location_term=str(
            (raw.get("terminology") or {}).get("location_term", "") or DEFAULT_LOCATION_TERM
        ),
    )


def get_cross_dc_config() -> CrossDcConfig:
    global _cache
    if _cache is None:
        with _lock:
            if _cache is None:
                _cache = load_cross_dc_config()
    return _cache


def set_cross_dc_config(config: CrossDcConfig | None) -> None:
    """测试注入点。传 None 清空缓存。"""
    global _cache
    with _lock:
        _cache = config
