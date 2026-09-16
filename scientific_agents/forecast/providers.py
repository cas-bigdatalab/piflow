"""Transport is replaceable; callers only consume timestamped variables + provenance."""
from dataclasses import dataclass
from contextlib import ExitStack, contextmanager
from typing import Protocol
import pandas as pd

from .config import Case, Settings, Source, Variable


@dataclass
class RawSeries:
    values: pd.Series
    provenance: dict
    available_at: pd.Series | None = None


class DataProvider(Protocol):
    """Required observation boundary; configure/auxiliary_variable are optional adapter hooks."""
    def read(self, case: Case, variable: Variable) -> RawSeries: ...


def read_csv_series(path, variable, provenance):
    """One parser for cloud snapshots and native bundles, preserving release times."""
    data = pd.read_csv(path)

    def times(column):
        index = pd.DatetimeIndex(pd.to_datetime(data[column], errors="raise"))
        if index.tz is None:
            index = index.tz_localize(variable.timezone, ambiguous="raise", nonexistent="raise")
        return index.tz_convert("UTC")

    index = times(variable.time_column)
    values = pd.to_numeric(data[variable.value_column], errors="raise") * variable.scale
    if variable.quality_column:
        if not variable.valid_quality_values:
            raise ValueError("质量列必须同时声明允许的质量标记")
        values = values.where(data[variable.quality_column].astype(str).isin(variable.valid_quality_values))
    available = times(variable.available_at_column) if variable.available_at_column else index
    if index.hasnans or available.hasnans:
        raise ValueError("观测时间或可用时间缺失")
    order = index.argsort()
    index = index[order]
    numeric = values.to_numpy(dtype=float)[order]
    if variable.transform == "unwrap_degrees":
        import numpy as np
        valid = np.flatnonzero(np.isfinite(numeric))
        for run in np.split(valid, np.flatnonzero(np.diff(valid) > 1) + 1):
            if len(run):
                numeric[run] = np.rad2deg(np.unwrap(np.deg2rad(numeric[run])))
        provenance = {**provenance, "derivation": "causal_unwrap_degrees; direction = angle modulo 360"}
    return RawSeries(pd.Series(numeric, index=index, name=variable.name),
        {**provenance, "unit": variable.unit, "scale": variable.scale, "aggregation": variable.aggregation,
         "availability": "explicit" if variable.available_at_column else "observation_time_assumed"},
        pd.Series(available[order], index=index))


def builtin_providers():
    from .resource_provider import ManifestCSVProvider
    from .ingest.campbell import CampbellProvider
    from .discovery import DirectoryProvider
    return {"local_csv": ManifestCSVProvider, "campbell_jsonl": CampbellProvider, "directory": DirectoryProvider}


class Registry:
    """Refreshable source catalogue with isolated per-task selections."""
    def __init__(self, settings: Settings, providers: dict[str, DataProvider] | None = None, factories=None):
        from .warning.registry import WarningRegistry
        self.warnings = WarningRegistry(settings)
        self.settings = settings
        self.source_specs, self.scenario_specs = settings.sources, settings.warning_scenarios
        import threading
        self.lock = threading.RLock()
        self.statuses, self.series_info, self.bindings = {}, {}, {}
        self.cases = {c.id: c for s in settings.sources for c in s.cases}
        self.case_sources = {c.id: s.id for s in settings.sources for c in s.cases}
        factories = factories or builtin_providers()
        self.factories = factories
        self.providers = {}
        self.source_providers = {}
        for source in settings.sources:
            supplied = (providers or {}).get(source.id)
            if supplied is None and source.kind not in factories:
                raise ValueError(f"未注册数据提供器：{source.kind}")
            provider = supplied or factories[source.kind](source, settings)
            self.source_providers[source.id] = provider
            self.providers.update({c.id: provider for c in source.cases})

    def refresh(self, *, reload_config=False):
        """Atomically replace the catalogue; a failed source cannot erase healthy ones."""
        import yaml
        from .config import Source, registry_entries
        from .warning.contracts import Scenario
        from .warning.registry import WarningRegistry
        with self.lock:
            sources, scenarios = self.source_specs, self.scenario_specs
            if reload_config and self.settings.registry_path:
                path = self.settings.registry_path
                raw, scenario_data = registry_entries(yaml.safe_load(path.read_text(encoding="utf-8")) or {}, path, self.factories)
                sources = [Source.model_validate(s) for s in raw]
                scenarios = [Scenario.model_validate(s) for s in scenario_data]
            cases, providers, statuses, info, instances = {}, {}, {}, {}, {}
            original_scenarios = {s.case_id: s for s in scenarios}
            all_scenarios = []
            for source in sources:
                provider = self.source_providers.get(source.id)
                if provider is None or (hasattr(provider, "source") and provider.source != source):
                    provider = self.factories[source.kind](source, self.settings)
                instances[source.id] = provider
                entries = [(c, {}) for c in source.cases]
                try:
                    if source.discover and hasattr(provider, "discover"):
                        entries = provider.discover()
                    statuses[source.id] = provider.catalog_status() if hasattr(provider, "catalog_status") else {"state": "ready"}
                except Exception as exc:
                    statuses[source.id] = {"state": "error", "message": str(exc)}
                    entries = [(c, {"state": "unavailable"}) for c in source.cases]
                statuses[source.id]["source_name"] = source.display_name or source.id
                for case, details in entries:
                    if case.id in cases:
                        raise ValueError("数据源目录出现重复变量编号")
                    cases[case.id], providers[case.id], info[case.id] = case, provider, details
                    scenario = original_scenarios.get(case.id)
                    if scenario is None and details:
                        frequency = details.get("frequency_minutes", self.settings.frequency_minutes)
                        base_scenario = next((original_scenarios[c.id] for c in source.cases if c.id in original_scenarios), None)
                        scenario = Scenario(case_id=case.id, version="discovered-1", area=case.station_id,
                            hazard_type="unspecified", mode=details.get("mode", base_scenario.mode if base_scenario else "current"), frequency_minutes=frequency,
                            default_replay_origin=details.get("default_replay_origin", base_scenario.default_replay_origin if base_scenario else None),
                            context_steps=max(8, 7 * 24 * 60 // frequency),
                            horizons_hours=[h for h in sorted(set([*self.settings.horizons_hours, 24, 48, 72]))
                                            if h * 60 % frequency == 0 and h * 60 // frequency <= 1024],
                            use_standard=True)
                    if scenario is not None and source.discover:
                        scenario = scenario.model_copy(update={"use_history_screening": True})
                    if scenario is not None:
                        all_scenarios.append(scenario)
            cfg = self.settings.model_copy(deep=True)
            # Keep rule definitions valid independently of this request's input selection.
            configured = {c.id: c for s in sources for c in s.cases}
            rule_cases = {key: c.model_copy(update={"covariates": configured[key].covariates}) if key in configured else c
                          for key, c in cases.items()}
            cfg.sources = [s.model_copy(update={"cases": [c for c in rule_cases.values() if providers[c.id] is instances[s.id]]}) for s in sources]
            cfg.warning_scenarios = all_scenarios
            warnings = WarningRegistry(cfg)
            self.cases, self.providers, self.warnings = cases, providers, warnings
            self.source_providers, self.statuses, self.series_info = instances, statuses, info
            self.source_specs, self.scenario_specs = sources, scenarios
            self.case_sources = {key: sid for key, p in providers.items() for sid, instance in instances.items() if p is instance}
            return {"sources": [{"id": s.id, **statuses[s.id], "variable_count": sum(p is instances[s.id] for p in providers.values())} for s in sources]}

    def bind(self, params):
        """Task-local catalogue and variable routing. Never edit shared case definitions."""
        from copy import copy
        from .feedback import ForecastError
        with self.lock:
            result = copy(self)
            result.cases = {k: c.model_copy(deep=True) for k, c in self.cases.items()}
            result.providers, result.bindings = dict(self.providers), {}
            # A directory provider's map points only to immutable local snapshots.
            copies = {}
            for key, provider in result.providers.items():
                if hasattr(provider, "entries") and hasattr(provider, "current"):
                    if id(provider) not in copies:
                        copies[id(provider)] = copy(provider)
                        copies[id(provider)].current = dict(provider.current)
                    result.providers[key] = copies[id(provider)]
            result.warnings = self.warnings
            if params.auxiliary_case_ids is None:
                legacy = {c.id: c for s in self.source_specs for c in s.cases}
                for key in params.case_ids:
                    if key in result.cases and key in legacy:
                        result.cases[key] = legacy[key].model_copy(deep=True)
            if params.auxiliary_case_ids is not None:
                if len(params.auxiliary_case_ids) > 16 or len(set(params.auxiliary_case_ids)) != len(params.auxiliary_case_ids):
                    raise ForecastError("invalid_parameters", "辅助变量最多16个且不能重复")
                if params.auxiliary_case_ids and len(params.case_ids) != 1:
                    raise ForecastError("invalid_parameters", "组合预测请选择一个目标和多个历史辅助变量")
                for key in params.case_ids:
                    if key not in result.cases:
                        raise ForecastError("invalid_parameters", "预测目标已不在当前目录，请刷新选择")
                    if self.series_info.get(key, {}).get("state") == "unavailable":
                        raise ForecastError("data_unavailable", "所选数据源刷新失败，请查看目录状态并修复数据源")
                    case = result.cases[key]
                    case.covariates = []
                    for auxiliary in params.auxiliary_case_ids:
                        if auxiliary == key or auxiliary not in self.cases:
                            raise ForecastError("invalid_parameters", "辅助变量不存在或与预测目标相同")
                        if self.series_info.get(auxiliary, {}).get("state") == "unavailable":
                            raise ForecastError("data_unavailable", "辅助变量的数据源当前不可用")
                        original = self.cases[auxiliary].target
                        adapt = getattr(result.providers[auxiliary], "auxiliary_variable", None)
                        if adapt:
                            original = adapt(original)
                        if original.transform == "unwrap_degrees":
                            original = original.model_copy(update={"transform": None, "semantics": "circular_degrees",
                                "minimum": 0, "maximum": 360})
                        target_frequency = self.warnings.timing(key)[0]
                        auxiliary_frequency = self.warnings.timing(auxiliary)[0]
                        if target_frequency % auxiliary_frequency:
                            raise ForecastError("invalid_parameters", "辅助变量频率需等于或细于目标频率，且能整倍数对齐；不自动插值")
                        if self.warnings.get(self.cases[auxiliary]).mode != self.warnings.get(case).mode:
                            raise ForecastError("invalid_parameters", "当前监测与历史回放数据不能混合使用")
                        variable = original.model_copy(update={"name": f"aux_{auxiliary}", "future_known": False})
                        case.covariates.append(variable)
                        result.bindings[(key, variable.name)] = (auxiliary, original)
            return result

    def list_cases(self) -> list[dict]:
        with self.lock:
            return self._list_cases()

    def display_metadata(self, case_id):
        case = self.cases[case_id]
        source = next((s for s in self.source_specs if s.id == self.case_sources.get(case_id)), None)
        location = case.location or (source.location if source else None)
        return {"source_name": (source.display_name or source.id) if source else "",
                "location": location.model_dump(mode="json") if location else None}

    def _list_cases(self):
        statuses = {id(p): self.statuses.get(sid) or (p.catalog_status() if hasattr(p, "catalog_status") else {})
                    for sid, p in self.source_providers.items()}
        return [dict(id=c.id, label=c.label, station_id=c.station_id,
                     **self.display_metadata(c.id),
                     source_id=self.case_sources.get(c.id, ""),
                     series_status=self.series_info.get(c.id, {}),
                     **({"data_status": statuses[id(self.providers[c.id])]} if id(self.providers[c.id]) in statuses else {}),
                     description=c.target.description, analysis_context=c.analysis_context.model_dump(mode="json"),
                     variable=c.target.name, variable_aliases=c.target.aliases, unit=c.target.unit,
                     covariates=[v.name for v in c.covariates],
                     area=self.warnings.get(c).area, hazard_type=self.warnings.get(c).hazard_type,
                     aliases=self.warnings.get(c).aliases, mode=self.warnings.get(c).mode,
                     hazard_aliases=self.warnings.get(c).hazard_aliases,
                     horizons_hours=self.warnings.timing(c.id)[2],
                     frequency_minutes=self.warnings.timing(c.id)[0], context_steps=self.warnings.timing(c.id)[1],
                     default_replay_origin=(self.warnings.get(c).default_replay_origin.isoformat() if self.warnings.get(c).default_replay_origin else None),
                     capability="rule_assessment" if any(r.approved for r in self.warnings.get(c).rules) else "indicator_forecast",
                     probability_available=False) for c in self.cases.values()]

    def read(self, case_id: str, variable: Variable) -> RawSeries:
        if (case_id, variable.name) in self.bindings:
            origin_id, original = self.bindings[(case_id, variable.name)]
            raw = self.providers[origin_id].read(self.cases[origin_id], original)
            display = self.display_metadata(origin_id)
        else:
            raw = self.providers[case_id].read(self.cases[case_id], variable)
            display = self.display_metadata(case_id)
        return RawSeries(raw.values, {**raw.provenance, **display}, raw.available_at)

    def history_end(self, case_id, origin, frequency, cache):
        provider = self.providers[case_id]
        if self.bindings or getattr(provider, "align_history", False):
            from .discovery import common_history_end
            case = self.cases[case_id]
            variables = [case.target, *case.covariates]
            for v in variables:
                if (case_id, v.name) not in cache:
                    cache[(case_id, v.name)] = self.read(case_id, v)
            return common_history_end([(cache[(case_id, v.name)], v) for v in variables], origin, frequency)
        if not hasattr(provider, "history_end"):
            return origin
        case = self.cases[case_id]
        for variable in [case.target, *case.covariates]:
            key = (case_id, variable.name)
            if key not in cache:
                cache[key] = self.read(case_id, variable)
        return provider.history_end(case, origin, frequency,
                                    {v.name: cache[(case_id, v.name)] for v in [case.target, *case.covariates]})

    @contextmanager
    def read_snapshot(self, case_ids):
        """Live adapters pin one prepared revision across all variables in a task."""
        with ExitStack() as stack:
            keys = [*case_ids, *(key for key, _ in self.bindings.values())]
            for provider in {id(self.providers[key]): self.providers[key] for key in keys}.values():
                if hasattr(provider, "snapshot"):
                    stack.enter_context(provider.snapshot())
            yield
