"""Requested windows select the existing sampling grid for every source and time unit."""
import logging
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from scientific_agents.forecast.analytics import resample_variable
from scientific_agents.forecast.config import Case, Settings, Source, Variable
from scientific_agents.forecast.feedback import ForecastError
from scientific_agents.forecast.planning import forecast_grid, sampling_floor
from scientific_agents.forecast.providers import RawSeries, Registry
from scientific_agents.forecast.schema import TaskParams
from scientific_agents.forecast.workflow import ForecastWorkflow


class RampModel:
    def metadata(self):
        return {"id": "test-only"}

    def predict(self, inputs, steps):
        self.inputs, self.steps = inputs, steps
        medians = np.arange(1, steps + 1, dtype=float)
        return [np.column_stack([medians - 1, medians, medians + 1]) for _ in inputs]


def workflow_for(tmp_path, frequency, origin, *, aggregation="mean", mode="historical_replay"):
    target = Variable(name="measurement", unit="unit", aggregation=aggregation)
    case = Case(id="generic", label="Generic source", station_id="any", target=target)
    source = Source(id="source", kind="memory", cases=[case])
    settings = Settings(sources=[source], root=tmp_path, frequency_minutes=frequency, context_steps=8,
        history_multiplier=1, horizons_hours=[1, 24], warning_scenarios=[{
            "case_id": case.id, "version": "test", "area": "any", "hazard_type": "unspecified",
            "mode": mode, "use_standard": False}])
    dates = pd.date_range(end=pd.Timestamp(origin).tz_convert("UTC").floor(f"{frequency}min"),
                          periods=1000, freq=f"{frequency}min")
    values = pd.Series(np.arange(len(dates), dtype=float), index=dates)
    raw = RawSeries(values, {})
    provider = SimpleNamespace(read=lambda *_: raw)
    registry = Registry(settings, providers={"source": provider})
    return ForecastWorkflow(settings, registry, RampModel()), raw


@pytest.mark.parametrize("frequency,hours,origin", [
    (7, 24, "2026-09-17T00:00:00+08:00"),
    (7, 1, "2026-09-17T10:02:37+08:00"),
    (17, 24, "2026-09-17T00:00:00+08:00"),
    (17, 1, "2026-09-17T10:02:37+08:00"),
    (30, 24, "2026-09-17T00:00:00+08:00"),
    (30, 1, "2026-09-17T10:02:37+08:00"),
    (180, 1, "2026-09-17T11:30:00Z"),
])
def test_general_windows_preserve_sampling_grid_and_value_alignment(tmp_path, monkeypatch, frequency, hours, origin):
    from piflow_engine.cn.piflow.core import stop_job

    monkeypatch.setattr(stop_job, "get_logger", lambda _: logging.getLogger(__name__))
    workflow, raw = workflow_for(tmp_path, frequency, origin)
    start = pd.Timestamp(origin)
    cutoff = start - pd.Timedelta(hours=3, minutes=2)
    params = TaskParams(case_ids=["generic"], origin=start, history_cutoff=cutoff, horizon_hours=hours)
    item = workflow.prepare(params)[0]
    history_end = sampling_floor(cutoff, frequency)
    assert pd.Timestamp(item["timestamps"][-1]) == history_end
    # Construct the expected grid independently, by extending historical observations then filtering.
    complete = pd.date_range(start=history_end, end=start.tz_convert("UTC") + pd.Timedelta(hours=hours), freq=f"{frequency}min")
    wanted = complete[complete > start]
    actual = pd.to_datetime(item["future"], utc=True)
    assert actual.tolist() == wanted.tolist()
    assert not (actual > start + pd.Timedelta(hours=hours)).any()
    assert item["quality"]["measurement"]["filled_points"] == 0
    assert "model_input" not in item  # This generic source never invokes the station completion policy.
    original_values = raw.values.copy(deep=True)
    result = workflow.run("grid-window", params, defer_report=True)
    series = result.series[0]
    skip = len(complete[(complete > history_end) & (complete <= start)])
    assert workflow.model.steps == len(complete) - 1
    assert [p.prediction for p in series.predictions] == list(range(skip + 1, len(complete)))
    assert len(series.forecast_context) == skip
    assert pd.Timestamp(series.assessment.window_start) == start
    assert pd.Timestamp(series.assessment.window_end) == start + pd.Timedelta(hours=hours)
    assert series.metadata["forecast_window"]["points"] == len(wanted)
    frame = pd.read_csv(tmp_path / "runs" / "grid-window" / "predictions.csv")
    assert pd.to_datetime(frame.timestamp, utc=True).tolist() == wanted.tolist()
    assert frame.prediction.tolist() == [p.prediction for p in series.predictions]
    assert series.summary["min"] == frame.prediction.min()
    from scientific_agents.forecast.warning.insights import periods

    blocks = periods(series)
    assert len(blocks) == 1
    assert pd.Timestamp(blocks[0]["start"]) == start
    assert pd.Timestamp(blocks[0]["end"]) == start + pd.Timedelta(hours=hours)
    assert blocks[0]["max"] == series.summary["max"]
    dates = pd.to_datetime([series.history[-1]["timestamp"], *[p.timestamp for p in series.predictions]], utc=True)
    values = [series.history[-1]["value"], *[p.prediction for p in series.predictions]]
    rates = np.diff(values) / ((dates[1:] - dates[:-1]).total_seconds().to_numpy() / 3600)
    assert result.research["features"][0]["largest_rate"]["value"] == pytest.approx(rates[np.abs(rates).argmax()])
    pd.testing.assert_series_equal(raw.values, original_values)


def test_adjacent_day_windows_have_no_duplicate_or_missing_samples():
    origin = pd.Timestamp("2026-09-17T00:00:00+08:00")
    first = forecast_grid(origin, 24, 7)
    second = forecast_grid(origin + pd.Timedelta(days=1), 24, 7)
    combined = forecast_grid(origin, 48, 7)
    assert first.intersection(second).empty
    assert first.append(second).tolist() == combined.tolist()
    assert len(first) != len(second)  # Do not assume floor(1440 / 7) for every day.


def test_empty_sampling_window_fails_clearly(tmp_path):
    workflow, _ = workflow_for(tmp_path, 180, "2026-09-17T09:01:00Z")
    with pytest.raises(ForecastError, match="没有采样点"):
        workflow.validate(TaskParams(case_ids=["generic"], origin="2026-09-17T09:01:00Z", horizon_hours=1))


def test_cutoff_excludes_incomplete_bins_and_does_not_relabel_accumulations(tmp_path):
    origin = pd.Timestamp("2026-09-17T10:02:37+08:00")
    workflow, raw = workflow_for(tmp_path, 7, origin, aggregation="sum")
    # Finer raw observations include a very large value after the last closed history bin.
    cutoff = origin.tz_convert("UTC").floor("7min")
    raw.values = pd.Series(1., index=pd.date_range(end=cutoff + pd.Timedelta(hours=2), periods=2000, freq="1min"))
    raw.values.loc[cutoff + pd.Timedelta(minutes=1)] = 99999
    params = TaskParams(case_ids=["generic"], origin=origin, horizon_hours=1)
    item = workflow.prepare(params)[0]
    assert len(item["target"]) >= 8 and set(item["target"]) == {7.}
    # Truth retains full right-labelled intervals, including the portion before the request instant.
    expected = resample_variable(raw.values, 7, workflow.registry.cases["generic"].target)
    dates = pd.to_datetime(item["future"], utc=True)
    assert item["observations"] == expected.reindex(dates).tolist()
    assert item["observations"][0] == 100005


def test_current_request_accepts_unaligned_wall_clock_without_future_input(tmp_path):
    now = pd.Timestamp.now(tz="UTC")
    workflow, _ = workflow_for(tmp_path, 7, now, mode="current")
    params = TaskParams(case_ids=["generic"], origin=now, horizon_hours=1)
    item = workflow.prepare(params)[0]
    assert pd.Timestamp(item["timestamps"][-1]) == now.floor("7min")
    assert pd.Timestamp(item["future"][0]) > now
    assert pd.Timestamp(item["future"][-1]) <= now + pd.Timedelta(hours=1)


def test_discovery_keeps_nondivisible_horizons_in_catalogue(tmp_path):
    workflow, _ = workflow_for(tmp_path, 7, "2026-09-17T00:00:00+08:00")
    source = workflow.settings.sources[0]
    source.discover = True
    discovered = source.cases[0].model_copy(update={"id": "discovered"})
    provider = workflow.registry.source_providers[source.id]
    provider.discover = lambda: [(discovered, {"frequency_minutes": 17, "mode": "historical_replay"})]
    workflow.registry.refresh()
    frequency, _, horizons = workflow.registry.warnings.timing(discovered.id)
    assert frequency == 17 and 1 in horizons and 24 in horizons


def test_multiple_targets_align_independently_in_shared_window(tmp_path):
    origin = pd.Timestamp("2026-09-17T10:02:37+08:00")
    workflow, first = workflow_for(tmp_path, 7, origin)
    cfg = workflow.settings
    other = cfg.sources[0].cases[0].model_copy(update={"id": "other"})
    cfg.sources[0].cases.append(other)
    cfg.warning_scenarios.append(cfg.warning_scenarios[0].model_copy(update={"case_id": "other", "frequency_minutes": 17}))
    dates = pd.date_range(end=origin.tz_convert("UTC").floor("17min"), periods=100, freq="17min")
    second = RawSeries(pd.Series(np.arange(100, dtype=float), index=dates), {})
    provider = SimpleNamespace(read=lambda case, _: first if case.id == "generic" else second)
    registry = Registry(cfg, providers={"source": provider})
    workflow = ForecastWorkflow(cfg, registry, RampModel())
    params = TaskParams(case_ids=["generic", "other"], origin=origin, horizon_hours=1)
    items = workflow.prepare(params)
    for item, frequency in zip(items, [7, 17]):
        assert pd.Timestamp(item["timestamps"][-1]) == origin.tz_convert("UTC").floor(f"{frequency}min")
        dates = pd.to_datetime(item["future"], utc=True)
        assert dates.tolist() == forecast_grid(origin, 1, frequency).tolist()
        assert pd.Timestamp(item["metadata"]["forecast_window"]["start"]) == origin
    assert len(items[0]["future"]) != len(items[1]["future"])


def test_report_daily_totals_use_time_boundaries_not_fixed_sample_counts():
    from scientific_agents.forecast.warning.insights import periods

    start = pd.Timestamp("2026-09-17T00:00:00+08:00")
    dates = forecast_grid(start, 48, 7)
    series = SimpleNamespace(predictions=[SimpleNamespace(timestamp=t.isoformat(), prediction=1.) for t in dates],
        metadata={"forecast_window": {"start": start.isoformat(), "end": (start + pd.Timedelta(days=2)).isoformat()}},
        variable="amount", quality={"amount": {"aggregation": "sum"}}, assessment=None)
    blocks = periods(series)
    assert len(blocks) == 2
    assert blocks[0]["total"] == len(forecast_grid(start, 24, 7))
    assert blocks[1]["total"] == len(forecast_grid(start + pd.Timedelta(days=1), 24, 7))
    assert blocks[0]["total"] + blocks[1]["total"] == len(dates)
    assert pd.Timestamp(blocks[0]["end"]) == pd.Timestamp(blocks[1]["start"])
