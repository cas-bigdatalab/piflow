"""数据源注册表 —— 临时桩实现。"""

from __future__ import annotations

import logging

import threading
from dataclasses import dataclass, field
from typing import Protocol

from .schema import BUNDLE_SOURCE_FILE


@dataclass(frozen=True)
class DataSourceRecord:
    """一个数据源/执行位置。

    ``ip`` 是历史字段名，现作为调度使用的规范位置 ID；它通常是主机名或 IP，
    但调用方不应假设它一定是 IPv4。``source_id`` 保留注册中心自己的业务 ID，
    ``grpc_endpoint`` 则是实际提交地址。三者分开后，连接器换 ID、域名或端口都不
    需要改调度代码。
    """

    ip: str
    name: str = ""
    status: str = "AVAILABLE"
    metrics: dict[str, float] = field(default_factory=dict)
    aliases: tuple[str, ...] = ()
    source_id: str = ""
    grpc_endpoint: str = ""

    @property
    def center_id(self) -> str:
        return self.ip

    def to_json(self) -> dict:
        return {
            "source_id": self.source_id or self.ip,
            "center_id": self.center_id,
            "ip": self.ip,
            "name": self.name,
            "status": self.status,
            "grpc_endpoint": self.grpc_endpoint,
            "metrics": dict(self.metrics),
            "aliases": list(self.aliases),
        }


@dataclass(frozen=True)
class ReplicaRecord:
    """数据集在某个数据源上的那一份。"""

    replica_id: str
    source_ip: str
    locator: str
    status: str = "AVAILABLE"
    metrics: dict[str, float] = field(default_factory=dict)

    def to_json(self) -> dict:
        return {
            "replica_id": self.replica_id,
            "source_ip": self.source_ip,
            "locator": self.locator,
            "status": self.status,
            "metrics": dict(self.metrics),
        }


@dataclass(frozen=True)
class DatasetRecord:
    """一个逻辑数据集，可能在多个数据源上各有一份。"""

    dataset_id: str
    name: str
    replicas: tuple[ReplicaRecord, ...] = ()
    description: str = ""
    tags: tuple[str, ...] = ()
    # 结构化元数据：维度键 -> 该数据集在这个维度上提供的取值。
    # 维度键由注册方定义，平台不预设；没声明的维度在需求满足分析里按"无法核实"处理。
    facets: dict[str, tuple[str, ...]] = field(default_factory=dict)
    # 读取契约随数据集注册，不由 LLM 猜。不同数据源类型可声明自己的输入算子和端口。
    source_skill: str = BUNDLE_SOURCE_FILE
    source_param: str = "file_path"
    source_output_param: str = "output"

    @property
    def primary(self) -> ReplicaRecord | None:
        """首选副本，仅用于展示与兜底；真正读哪份由 selector 决定。"""
        available = [r for r in self.replicas if r.status.upper() == "AVAILABLE"]
        pool = available or list(self.replicas)
        return pool[0] if pool else None

    @property
    def source_id(self) -> str:
        return self.primary.source_ip if self.primary else ""

    @property
    def center_id(self) -> str:
        return self.primary.source_ip if self.primary else ""

    @property
    def locator(self) -> str:
        return self.primary.locator if self.primary else ""

    def to_json(self) -> dict:
        return {
            "dataset_id": self.dataset_id,
            "name": self.name,
            "description": self.description,
            "tags": list(self.tags),
            "facets": {k: list(v) for k, v in self.facets.items()},
            "access": {
                "skill": self.source_skill,
                "param": self.source_param,
                "output_param": self.source_output_param,
            },
            "replicas": [r.to_json() for r in self.replicas],
        }


class DatasourceRegistry(Protocol):
    def list_sources(self) -> list[DataSourceRecord]: ...

    def list_datasets(self) -> list[DatasetRecord]: ...

    def get_dataset(self, dataset_id: str) -> DatasetRecord | None: ...

    def list_replicas(self, dataset_id: str) -> list[ReplicaRecord]: ...

    def get_center_of_source(self, source_id: str) -> str | None: ...

    def search_datasets(self, keywords: list[str], limit: int = 8) -> list[DatasetRecord]: ...


_DEMO_SOURCES: tuple[DataSourceRecord, ...] = (
    DataSourceRecord(
        ip="10.0.1.10",
        name="北京数据源",
        metrics={"cpu_cores": 64, "memory_gb": 256},
        aliases=("北京", "京区"),
    ),
    DataSourceRecord(
        ip="10.0.2.10",
        name="新疆数据源",
        metrics={"cpu_cores": 128, "memory_gb": 512},
        aliases=("新疆", "疆区"),
    ),
    DataSourceRecord(
        ip="10.0.3.10",
        name="广州数据源",
        status="MAINTENANCE",
        metrics={"cpu_cores": 32, "memory_gb": 128},
        aliases=("广州", "穗区"),
    ),
)

# facets 的键由注册方定义，这里用地学场景举例；其他学科用自己的键即可，
# 平台侧不认识具体含义，只做取值集合的比对。
_DEMO_DATASETS: tuple[DatasetRecord, ...] = (
    DatasetRecord(
        dataset_id="ds-obs",
        name="地面气象观测原始数据",
        description="地面气象观测原始记录，含站点号、时间、气温、降水。三个数据源各有一份。",
        tags=("观测", "气象", "原始数据"),
        facets={
            "variables": ("气温", "降水"),
            "region": ("长江流域",),
            "time_range": ("2020-2025",),
            "temporal_scale": ("日",),
        },
        replicas=(
            ReplicaRecord("rep-obs-bj", "10.0.1.10", "/data/obs/obs_raw.csv"),
            ReplicaRecord("rep-obs-xj", "10.0.2.10", "/mirror/obs/obs_raw.csv"),
            ReplicaRecord("rep-obs-gz", "10.0.3.10", "/archive/obs_raw.csv"),
        ),
    ),
    DatasetRecord(
        dataset_id="ds-prec",
        name="长江流域逐日降水数据集",
        description="长江流域 2020-2025 年逐日降水观测，覆盖流域内主要气象站点。",
        tags=("气象", "降水", "逐日"),
        facets={
            "variables": ("降水",),
            "region": ("长江流域",),
            "time_range": ("2020-2025",),
            "temporal_scale": ("日",),
        },
        replicas=(
            ReplicaRecord("rep-prec-bj", "10.0.1.10", "/data/prec/daily.csv"),
            ReplicaRecord("rep-prec-xj", "10.0.2.10", "/mirror/prec/daily.csv"),
        ),
    ),
    DatasetRecord(
        dataset_id="ds-soil",
        name="长江流域土壤湿度观测数据集",
        description="长江流域 2020-2025 年逐日土壤湿度观测，含多层深度。",
        tags=("土壤", "湿度", "逐日"),
        facets={
            "variables": ("土壤湿度",),
            "region": ("长江流域",),
            "time_range": ("2020-2025",),
            "temporal_scale": ("日",),
        },
        replicas=(
            ReplicaRecord("rep-soil-bj", "10.0.1.10", "/data/soil/moisture.csv"),
            ReplicaRecord("rep-soil-xj", "10.0.2.10", "/mirror/soil/moisture.csv"),
        ),
    ),
    DatasetRecord(
        dataset_id="ds-ndvi",
        name="长江流域NDVI遥感时序数据集",
        description="长江流域 2020-2025 年 NDVI 卫星遥感时序，250m 分辨率、16 天合成。",
        tags=("遥感", "NDVI", "时序"),
        facets={
            "variables": ("NDVI",),
            "region": ("长江流域",),
            "time_range": ("2020-2025",),
            "temporal_scale": ("16天",),
        },
        replicas=(
            ReplicaRecord("rep-ndvi-bj", "10.0.1.10", "/data/ndvi/ts.tif"),
            ReplicaRecord("rep-ndvi-xj", "10.0.2.10", "/mirror/ndvi/ts.tif"),
        ),
    ),
    DatasetRecord(
        dataset_id="ds-meta",
        name="气象站点元信息",
        description="气象站点元信息，含站点号、站名、省份。",
        tags=("站点", "元信息", "台站"),
        facets={"variables": ("站点元信息",), "region": ("长江流域",)},
        replicas=(
            ReplicaRecord("rep-meta-bj", "10.0.1.10", "/data/meta/station.csv"),
            ReplicaRecord("rep-meta-xj", "10.0.2.10", "/mirror/meta/station.csv"),
        ),
    ),
    DatasetRecord(
        dataset_id="ds-qc-rules",
        name="观测质控规则表",
        description="观测数据的质控阈值规则。",
        tags=("质控", "规则"),
        facets={"variables": ("质控规则",)},
        replicas=(ReplicaRecord("rep-qc-bj", "10.0.1.10", "/data/qc/rules.csv"),),
    ),
)


class StubDatasourceRegistry:
    """内存桩。真实注册表接入后整体替换。"""

    def __init__(
        self,
        sources: tuple[DataSourceRecord, ...] = _DEMO_SOURCES,
        datasets: tuple[DatasetRecord, ...] = _DEMO_DATASETS,
    ):
        self._sources = {item.ip: item for item in sources}
        self._datasets = {item.dataset_id: self._merge(item) for item in datasets}

    def _merge(self, dataset: DatasetRecord) -> DatasetRecord:
        """把数据源级的状态与资源指标合并进各副本。"""
        merged = []
        for replica in dataset.replicas:
            source = self._sources.get(replica.source_ip)
            if source is None:
                merged.append(replica)
                continue
            merged.append(
                ReplicaRecord(
                    replica_id=replica.replica_id,
                    source_ip=replica.source_ip,
                    locator=replica.locator,
                    status=(
                        replica.status
                        if source.status.upper() == "AVAILABLE"
                        else source.status
                    ),
                    metrics={**source.metrics, **replica.metrics},
                )
            )
        return DatasetRecord(
            dataset_id=dataset.dataset_id,
            name=dataset.name,
            replicas=tuple(merged),
            description=dataset.description,
            tags=dataset.tags,
            facets=dict(dataset.facets),
            source_skill=dataset.source_skill,
            source_param=dataset.source_param,
            source_output_param=dataset.source_output_param,
        )

    def list_sources(self) -> list[DataSourceRecord]:
        return list(self._sources.values())

    def list_datasets(self) -> list[DatasetRecord]:
        return list(self._datasets.values())

    def get_dataset(self, dataset_id: str) -> DatasetRecord | None:
        return self._datasets.get(dataset_id)

    def list_replicas(self, dataset_id: str) -> list[ReplicaRecord]:
        record = self._datasets.get(dataset_id)
        return list(record.replicas) if record else []

    def get_center_of_source(self, source_id: str) -> str | None:
        """数据源标识就是执行位置标识（都是 IP）。"""
        return source_id if source_id in self._sources else None

    def search_datasets(self, keywords: list[str], limit: int = 8) -> list[DatasetRecord]:
        """朴素打分检索。注册方自带检索接口时应转发过去，效果更好。"""
        normalized = [k.strip().lower() for k in keywords if k and k.strip()]
        if not normalized:
            return list(self._datasets.values())[:limit]

        scored: list[tuple[int, DatasetRecord]] = []
        for item in self._datasets.values():
            haystack = " ".join(
                [item.name, item.description, " ".join(item.tags), item.dataset_id]
            ).lower()
            score = sum(1 for key in normalized if key in haystack)
            if score:
                scored.append((score, item))

        scored.sort(key=lambda pair: (-pair[0], pair[1].dataset_id))
        return [item for _, item in scored[:limit]]


_registry: DatasourceRegistry | None = None
log = logging.getLogger("flow.cross_dag.registry")

_lock = threading.Lock()


def get_registry() -> DatasourceRegistry:
    global _registry
    if _registry is None:
        with _lock:
            if _registry is None:
                _registry = _build_default_registry()
    return _registry


def refresh_registry(registry: DatasourceRegistry | None = None) -> DatasourceRegistry:
    """Refresh a dynamic registry once and return the same registry instance.

    Registry implementations may expose a cached, request-scoped snapshot
    through ``refresh()``. Keeping this optional preserves the in-memory/test
    implementations while ensuring a long-running service does not keep using
    the connector list captured at process startup.
    """
    resolved = registry or get_registry()
    refresh = getattr(resolved, "refresh", None)
    if callable(refresh):
        refresh()
    return resolved


def _build_default_registry() -> DatasourceRegistry:
    """默认注册表：配置里给了语料系统地址就接真表，否则用演示桩。

    单测和演示要用桩，走 set_registry() 显式注入 —— 那是明确的意图表达，
    不该靠"接不上就退化"这种隐式行为来达成。
    """
    try:
        from infra.config_loader import get_settings

        base_url = str(get_settings().corpus_route.base_url or "").strip()
    except Exception:
        base_url = ""

    if not base_url:
        log.info("未配置 corpus_route.base_url，跨域调度使用演示桩数据源")
        return StubDatasourceRegistry()

    from .corpus_registry import build_corpus_registry

    # 接不上就抛出去，不回落到桩。
    # 回落看着"更健壮"，实际是拿演示数据冒充线上目录：用户会收到一份引用了
    # 不存在数据集的方案，还以为平台真有这些数据。数据源不可用是个诚实的错误，
    # 假数据不是。只有压根没配 corpus_route 时才用桩（那是演示部署）。
    registry = build_corpus_registry(base_url=base_url)
    # Keep construction lazy. The planning entry point refreshes and loads one
    # coherent snapshot; eagerly counting here would fetch/probe the complete
    # live directory twice for the first request.
    log.info("跨域调度已配置语料寻址系统 %s", base_url)
    return registry


def set_registry(registry: DatasourceRegistry | None) -> None:
    """替换注册表实现。真实注册表接入点 / 测试注入点。"""
    global _registry
    with _lock:
        _registry = registry
