"""数据源注册对接模板。"""

from __future__ import annotations

import logging
from typing import Any, Callable, Iterable

from .registry_stub import DatasetRecord, DataSourceRecord, ReplicaRecord

log = logging.getLogger("flow.cross_dag.registry_adapter")


class CallbackDatasourceRegistry:
    """把「拉取原始注册信息」和「字段映射」拆开的通用适配器。"""

    def __init__(
        self,
        fetch_sources: Callable[[], Iterable[Any]],
        source_mapper: Callable[[Any], DataSourceRecord | None],
        fetch_datasets: Callable[[], Iterable[Any]],
        dataset_mapper: Callable[[Any], DatasetRecord | None],
        *,
        cache: bool = True,
    ):
        self._fetch_sources = fetch_sources
        self._source_mapper = source_mapper
        self._fetch_datasets = fetch_datasets
        self._dataset_mapper = dataset_mapper
        self._cache_enabled = cache
        self._sources: dict[str, DataSourceRecord] | None = None
        self._datasets: dict[str, DatasetRecord] | None = None


    def list_sources(self) -> list[DataSourceRecord]:
        return list(self._all_sources().values())

    def list_datasets(self) -> list[DatasetRecord]:
        return list(self._all_datasets().values())

    def get_dataset(self, dataset_id: str) -> DatasetRecord | None:
        return self._all_datasets().get(dataset_id)

    def list_replicas(self, dataset_id: str) -> list[ReplicaRecord]:
        record = self._all_datasets().get(dataset_id)
        return list(record.replicas) if record else []

    def get_center_of_source(self, source_id: str) -> str | None:
        """数据源标识就是执行位置标识（都是 IP）。"""
        return source_id if source_id in self._all_sources() else None

    def search_datasets(self, keywords: list[str], limit: int = 8) -> list[DatasetRecord]:
        """默认按名称/描述/标签做关键词计分。"""
        normalized = [k.strip().lower() for k in keywords if k and k.strip()]
        records = list(self._all_datasets().values())
        if not normalized:
            return records[:limit]

        scored: list[tuple[int, DatasetRecord]] = []
        for item in records:
            haystack = " ".join(
                [item.name, item.description, " ".join(item.tags), item.dataset_id]
            ).lower()
            score = sum(1 for key in normalized if key in haystack)
            if score:
                scored.append((score, item))
        scored.sort(key=lambda pair: (-pair[0], pair[1].dataset_id))
        return [item for _, item in scored[:limit]]


    def refresh(self) -> None:
        """清空缓存，下次访问重新拉取。"""
        self._sources = None
        self._datasets = None

    def _all_sources(self) -> dict[str, DataSourceRecord]:
        if self._sources is not None:
            return self._sources

        sources: dict[str, DataSourceRecord] = {}
        for raw in self._fetch_sources() or []:
            try:
                record = self._source_mapper(raw)
            except Exception:
                log.warning("数据源映射失败，已跳过: %r", raw, exc_info=True)
                continue
            if record is None or not record.ip:
                continue
            sources[record.ip] = record

        if self._cache_enabled:
            self._sources = sources
        return sources

    def _all_datasets(self) -> dict[str, DatasetRecord]:
        if self._datasets is not None:
            return self._datasets

        sources = self._all_sources()
        datasets: dict[str, DatasetRecord] = {}
        for raw in self._fetch_datasets() or []:
            try:
                record = self._dataset_mapper(raw)
            except Exception:
                log.warning("数据集映射失败，已跳过: %r", raw, exc_info=True)
                continue
            if record is None or not record.dataset_id:
                continue
            datasets[record.dataset_id] = _merge_source_metrics(record, sources)

        if self._cache_enabled:
            self._datasets = datasets
        return datasets


def _merge_source_metrics(
    dataset: DatasetRecord,
    sources: dict[str, DataSourceRecord],
) -> DatasetRecord:
    """把数据源级的状态与资源指标合并进各副本。"""
    merged = []
    for replica in dataset.replicas:
        source = sources.get(replica.source_ip)
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


def check_registry(registry: Any, *, scored_metrics: Iterable[str] = ()) -> list[str]:
    """接入自检：返回问题清单，空列表表示可用。"""
    problems: list[str] = []

    for method in ("list_sources", "list_datasets", "get_dataset", "list_replicas",
                   "get_center_of_source", "search_datasets"):
        if not callable(getattr(registry, method, None)):
            problems.append(f"缺少协议方法: {method}()")
    if problems:
        return problems

    try:
        sources = {s.ip: s for s in registry.list_sources()}
        datasets = registry.list_datasets()
    except Exception as exc:
        return [f"注册表调用失败: {type(exc).__name__}: {exc}"]

    if not sources:
        problems.append("没有任何数据源")
    if not datasets:
        problems.append("没有任何数据集，意图识别将无数据可选")
    if problems:
        return problems

    wanted = [m for m in scored_metrics if m != "locality"]

    for source in sources.values():
        if not source.ip:
            problems.append("存在没有 ip 的数据源")
        for metric in wanted:
            if metric not in source.metrics:
                problems.append(
                    f"数据源 {source.ip}: 缺少打分指标 {metric}，该维度会按最差计分"
                )

    for item in datasets:
        if not item.dataset_id:
            problems.append("存在没有 dataset_id 的数据集")
            continue
        if not item.replicas:
            problems.append(f"数据集 {item.dataset_id} 没有任何副本，规划时必然失败")
            continue
        for replica in item.replicas:
            where = f"{item.dataset_id}/{replica.replica_id or '<无id>'}"
            if not replica.replica_id:
                problems.append(f"{where}: 缺少 replica_id")
            if not replica.source_ip:
                problems.append(f"{where}: 缺少 source_ip（必填，决定执行位置）")
            elif replica.source_ip not in sources:
                problems.append(f"{where}: source_ip={replica.source_ip} 不在数据源清单里")
            if not replica.locator:
                problems.append(f"{where}: 缺少 locator（访问路径）")

    return problems
