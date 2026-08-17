"""数据源注册表 —— 临时桩实现。"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import Protocol


@dataclass(frozen=True)
class DataSourceRecord:
    """一个数据源。"""

    ip: str
    name: str = ""
    status: str = "AVAILABLE"
    metrics: dict[str, float] = field(default_factory=dict)
    aliases: tuple[str, ...] = ()

    def to_json(self) -> dict:
        return {
            "ip": self.ip,
            "name": self.name,
            "status": self.status,
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

_DEMO_DATASETS: tuple[DatasetRecord, ...] = (
    DatasetRecord(
        dataset_id="ds-obs",
        name="地面气象观测原始数据",
        description="地面气象观测原始记录，含站点号、时间、气温。三个数据源各有一份。",
        tags=("观测", "气象", "原始数据"),
        replicas=(
            ReplicaRecord("rep-obs-bj", "10.0.1.10", "/data/obs/obs_raw.csv"),
            ReplicaRecord("rep-obs-xj", "10.0.2.10", "/mirror/obs/obs_raw.csv"),
            ReplicaRecord("rep-obs-gz", "10.0.3.10", "/archive/obs_raw.csv"),
        ),
    ),
    DatasetRecord(
        dataset_id="ds-meta",
        name="气象站点元信息",
        description="气象站点元信息，含站点号、站名、省份。",
        tags=("站点", "元信息", "台站"),
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
_lock = threading.Lock()


def get_registry() -> DatasourceRegistry:
    global _registry
    if _registry is None:
        with _lock:
            if _registry is None:
                _registry = StubDatasourceRegistry()
    return _registry


def set_registry(registry: DatasourceRegistry | None) -> None:
    """替换注册表实现。真实注册表接入点 / 测试注入点。"""
    global _registry
    with _lock:
        _registry = registry
