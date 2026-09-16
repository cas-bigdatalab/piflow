"""Public data boundary. Registration backends may replace this without changing prediction."""
from typing import Callable

import pandas as pd

from .config import Settings, Source
from .providers import DataProvider, RawSeries, Registry, builtin_providers


class ProviderFactories:
    """Plugins register transport factories explicitly; no dynamic code from user requests."""
    def __init__(self):
        self.factories: dict[str, Callable[[Source, Settings], DataProvider]] = builtin_providers()

    def register(self, kind: str, factory: Callable[[Source, Settings], DataProvider]):
        if kind in self.factories:
            raise ValueError(f"数据源类型已注册：{kind}")
        self.factories[kind] = factory

    def build(self, settings: Settings) -> Registry:
        providers = {}
        for source in settings.sources:
            if source.kind not in self.factories:
                raise ValueError(f"未注册的数据源类型：{source.kind}")
            providers[source.id] = self.factories[source.kind](source, settings)
        return Registry(settings, providers, self.factories)


class DataCatalog:
    def __init__(self, registry: Registry):
        self.registry = registry

    def list_cases(self):
        return self.registry.list_cases()

    def describe_series(self, case_id: str):
        case = self.registry.cases[case_id]
        variables = [case.target, *case.covariates]
        return {"case_id": case_id, "station_id": case.station_id,
                **self.registry.display_metadata(case_id),
                "target": case.target.name, "variables": [v.model_dump(exclude={"file"}) for v in variables],
                "scenario": self.registry.warnings.get(case).model_dump(mode="json")}

    def fetch_history(self, case_id: str, variable_name: str, *, start: str, as_of: str) -> RawSeries:
        return self._window(case_id, variable_name, start, as_of, include_start=True)

    def fetch_observations(self, case_id: str, *, after: str, end: str) -> RawSeries:
        return self._window(case_id, self.registry.cases[case_id].target.name, after, end, include_start=False)

    def _window(self, case_id, name, start, end, include_start):
        left, right = pd.Timestamp(start), pd.Timestamp(end)
        if left.tzinfo is None or right.tzinfo is None or left > right:
            raise ValueError("时间窗口必须包含时区且起点不晚于终点")
        case = self.registry.cases[case_id]
        variable = next((v for v in [case.target, *case.covariates] if v.name == name), None)
        if variable is None:
            raise ValueError("数据集中不存在该变量")
        raw = self.registry.read(case_id, variable)
        selected = raw.values.index >= left if include_start else raw.values.index > left
        selected &= raw.values.index <= right
        if include_start and raw.available_at is not None:
            selected &= (raw.available_at <= right).to_numpy()
        values = raw.values.iloc[selected].copy()
        available = raw.available_at.iloc[selected].copy() if raw.available_at is not None else None
        return RawSeries(values, dict(raw.provenance), available)
