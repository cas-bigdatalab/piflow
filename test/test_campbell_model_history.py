"""Station gap completion is confined to model inputs, not observations or other sources."""
import json
import logging
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from scientific_agents.forecast.config import Case, Settings, Source, Variable
from scientific_agents.forecast.feedback import ForecastError
from scientific_agents.forecast.ingest.campbell import CampbellProvider
from scientific_agents.forecast.providers import RawSeries, Registry
from scientific_agents.forecast.schema import TaskParams
from scientific_agents.forecast.workflow import ForecastWorkflow


def series(times, values):
    return pd.Series(values, index=pd.to_datetime(times, utc=True), dtype=float)


def test_completion_uses_only_earlier_real_values_and_preserves_input():
    variable = Variable(name="temperature", unit="degC")
    history = series(["2025-01-01 00:00", "2025-01-02 00:00", "2025-01-02 20:00", "2025-01-03 02:00"],
                     [10, 20, 40, 999])
    before = history.copy(deep=True)
    grid = pd.date_range("2025-01-03 00:00", periods=3, freq="30min", tz="UTC")
    result, quality = CampbellProvider.prepare_history(variable, history, grid)
    assert result.tolist() == [15, 40, 40]
    changed_future = history.copy()
    changed_future.iloc[-1] = -999
    pd.testing.assert_series_equal(result, CampbellProvider.prepare_history(variable, changed_future, grid)[0])
    pd.testing.assert_series_equal(history, before)
    assert quality["filled_points"] == 3
    assert quality["original_observations_preserved"]


def test_rain_uses_interval_median_instead_of_carrying_storm_forward_or_assuming_zero():
    variable = Variable(name="rain", unit="mm", aggregation="sum", minimum=0)
    history = series(["2025-01-01 00:00", "2025-01-01 00:30", "2025-01-01 01:00"], [2, 4, 100])
    grid = pd.date_range(history.index[0], periods=6, freq="30min")
    result, quality = CampbellProvider.prepare_history(variable, history, grid)
    assert result.tolist() == [2, 4, 100, 4, 4, 4]
    assert quality["filled_points"] == 3


@pytest.mark.parametrize("unwrapped", [False, True])
def test_direction_respects_circular_geometry_and_unwrapped_branch(unwrapped):
    variable = Variable(name="wind", unit="degree", semantics="scalar" if unwrapped else "circular_degrees",
                        transform="unwrap_degrees" if unwrapped else None)
    history = series(["2025-01-01 00:00", "2025-01-02 00:00", "2025-01-02 20:00"],
                     [719, 721, 710] if unwrapped else [359, 1, 350])
    grid = pd.date_range("2025-01-03 00:00", periods=2, freq="30min", tz="UTC")
    result, _ = CampbellProvider.prepare_history(variable, history, grid)
    if unwrapped:
        assert result.iloc[0] == pytest.approx(720)
    else:
        assert min(abs(result.iloc[0]), abs(result.iloc[0] - 360)) < 1e-8


def test_completion_does_not_invent_history_before_first_record_or_use_an_empty_channel():
    variable = Variable(name="temperature", unit="degC")
    grid = pd.date_range("2025-01-01", periods=8, freq="30min", tz="UTC")
    history = pd.Series([10.0], index=grid[4:5])
    result, _ = CampbellProvider.prepare_history(variable, history, grid)
    assert result.iloc[:4].isna().all()
    assert result.iloc[4:].tolist() == [10] * 4
    empty, _ = CampbellProvider.prepare_history(variable, history * np.nan, grid)
    assert empty.isna().all()


class RecordingModel:
    def metadata(self):
        return {"id": "test-only"}

    def predict(self, inputs, steps):
        self.inputs, self.steps = inputs, steps
        for item in inputs:
            assert np.isfinite(item["target"]).all()
            assert all(np.isfinite(v).all() for v in item["past_covariates"].values())
        return [np.tile([10., 15., 20.], (steps, 1)) for _ in inputs]


@pytest.fixture
def station(tmp_path):
    directory = tmp_path / "source"
    # Ten days of 08:30-17:30 records; the absent nights are intentional.
    for day in pd.date_range("2025-01-01", periods=10, tz="Asia/Shanghai"):
        dates = pd.date_range(day + pd.Timedelta(hours=8, minutes=30), periods=19, freq="30min")
        path = directory / str(day.date()) / "observations.jsonl"
        path.parent.mkdir(parents=True)
        path.write_text("".join(json.dumps({"timestamp": t.isoformat(), "TA_Avg": 10 + i / 2, "RH_Avg": 40 + i}) + "\n"
                                for i, t in enumerate(dates)), encoding="utf-8")
    target = Variable(name="air_temperature", value_column="TA_Avg", unit="degC", timezone="Asia/Shanghai")
    auxiliary = Variable(name="humidity", value_column="RH_Avg", unit="%", minimum=0, maximum=100, timezone="Asia/Shanghai")
    case = Case(id="temperature", label="Station temperature", station_id="station", target=target, covariates=[auxiliary])
    source = Source(id="station", kind="campbell_jsonl", options={"directory": str(directory)}, cases=[case])
    settings = Settings(sources=[source], root=tmp_path / "cache", frequency_minutes=30, context_steps=336,
                        history_multiplier=1, horizons_hours=[24], warning_scenarios=[{
                            "case_id": case.id, "version": "test", "area": "station", "hazard_type": "unspecified",
                            "mode": "historical_replay", "use_standard": False}])
    registry = Registry(settings)
    model = RecordingModel()
    workflow = ForecastWorkflow(settings, registry, model)
    params = TaskParams(case_ids=[case.id], origin=pd.Timestamp("2025-01-09 17:30+08:00").to_pydatetime(),
                        horizon_hours=24, history_hours=168)
    return SimpleNamespace(directory=directory, settings=settings, registry=registry, model=model,
                           workflow=workflow, params=params, case=case)


def test_night_gaps_are_completed_only_for_model_and_original_files_and_cache_are_unchanged(station):
    original_files = {p: p.read_bytes() for p in station.directory.rglob("*.jsonl")}
    provider = station.registry.providers[station.case.id]
    path, status = provider.refresh(force=True)
    original_csv = path.read_bytes()
    original = station.registry.read(station.case.id, station.case.target)
    prepared = station.workflow.prepare(station.params)
    item = prepared[0]
    assert len(item["target"]) == 336
    assert len(item["model_input"]["target"]) == 336
    assert sum(v is None for v in item["target"]) > 150
    assert all(v is not None for v in item["model_input"]["target"])
    for name in ("air_temperature", "humidity"):
        assert item["quality"][name]["filled_points"] > 150
        assert item["quality"][name]["filled_points"] == item["quality"][name]["missing_before"]
    expected_truth = original.values.reindex(pd.to_datetime(item["future"]))
    assert item["observations"] == [None if pd.isna(v) else float(v) for v in expected_truth]
    assert any(v is None for v in item["observations"])
    station.workflow.predict_prepared(prepared)
    np.testing.assert_allclose(station.model.inputs[0]["target"], item["model_input"]["target"])
    assert set(station.model.inputs[0]) == {"target", "past_covariates"}
    assert path.read_bytes() == original_csv
    assert provider.status["latest_observation"] == status["latest_observation"]
    for p, content in original_files.items():
        assert p.read_bytes() == content
    pd.testing.assert_series_equal(station.registry.read(station.case.id, station.case.target).values, original.values)
    json.dumps(item, allow_nan=False)


def test_display_history_is_continuous_but_evaluation_keeps_real_observations(station, monkeypatch, tmp_path):
    from piflow_engine.cn.piflow.core import stop_job

    monkeypatch.setattr(stop_job, "get_logger", lambda _: logging.getLogger(__name__))
    result = station.workflow.run("test-campbell-input", station.params, defer_report=True)
    output = result.series[0]
    assert len(output.history) == 336
    assert all(p["value"] is not None for p in output.history)
    assert sum(p["observed_value"] is None for p in output.history) > 150
    assert sum(p["imputed"] for p in output.history) > 150
    assert all(p["value"] == p["observed_value"] for p in output.history if not p["imputed"])
    assert output.evaluation["valid_points"] == 19
    assert output.evaluation["expected_points"] == 48
    assert output.summary["last_observation"] == 19
    assert output.quality["air_temperature"]["original_observations_preserved"]
    assert not any("补值" in message for message in result.presentation["series"][0]["warnings"])
    np.testing.assert_allclose([p["value"] for p in output.history], station.model.inputs[0]["target"])
    # The shared PNG/SVG images feed both the online and PDF reports.
    from scientific_agents.forecast.reports import _figures
    from matplotlib.axes import Axes

    plots = []
    original_plot = Axes.plot

    def capture(ax, *args, **kwargs):
        plots.append((args, kwargs))
        return original_plot(ax, *args, **kwargs)

    monkeypatch.setattr(Axes, "plot", capture)
    images = _figures(result, tmp_path)
    history_line = next((args, opts) for args, opts in plots if opts.get("color") == "#64748b")
    assert np.isfinite(np.asarray(history_line[0][1], dtype=float)).all()
    assert history_line[1]["label"] in {"近期历史", "Recent history"}
    assert (tmp_path / images[0][0]).stat().st_size > 0


def test_other_sources_retain_missing_data_rejection(station):
    raw = station.registry.read(station.case.id, station.case.target)
    provider = SimpleNamespace(read=lambda case, variable: raw)
    registry = Registry(station.settings, providers={"station": provider})
    workflow = ForecastWorkflow(station.settings, registry, station.model)
    with pytest.raises(ForecastError, match="缺测"):
        workflow.prepare(station.params)


def test_history_policy_follows_auxiliary_source_ownership(station):
    registry = station.registry
    registry.providers["other"] = SimpleNamespace()
    variable = station.case.target.model_copy(update={"name": "auxiliary"})
    grid = pd.date_range("2025-01-03", periods=8, freq="30min", tz="UTC")
    history = pd.Series([10.], index=grid[:1])
    registry.bindings[(station.case.id, variable.name)] = ("other", variable)
    assert registry.prepare_history(station.case.id, variable, history, grid) is None
    registry.bindings[("other", variable.name)] = (station.case.id, station.case.target)
    completed, _ = registry.prepare_history("other", variable, history, grid)
    assert completed.notna().all()
    assert registry.prepare_history(station.case.id, variable.model_copy(update={"future_known": True}), history, grid) is None


def test_current_freshness_is_not_hidden_by_input_completion(station):
    station.settings.warning_scenarios[0].mode = "current"
    workflow = ForecastWorkflow(station.settings, Registry(station.settings), station.model)
    params = station.params.model_copy(update={"origin": pd.Timestamp.now(tz="UTC").floor("30min").to_pydatetime()})
    with pytest.raises(ForecastError, match="过期"):
        workflow.prepare(params)


def test_current_prediction_keeps_real_history_end_and_forecasts_across_delay(station):
    origin = pd.Timestamp.now(tz="UTC").floor("30min")
    last_observed = origin - pd.Timedelta(hours=4)
    original = station.registry.read(station.case.id, station.case.target).values
    shifted = original.copy()
    shifted.index = shifted.index + (last_observed - shifted.index.max())

    class MemoryStation:
        options = SimpleNamespace(bridge_delayed_observations=True)
        prepare_history = staticmethod(CampbellProvider.prepare_history)
        history_end = CampbellProvider.history_end

        def read(self, case, variable):
            return RawSeries(shifted.copy(), {})

    station.settings.warning_scenarios[0].mode = "current"
    registry = Registry(station.settings, providers={"station": MemoryStation()})
    workflow = ForecastWorkflow(station.settings, registry, station.model)
    params = station.params.model_copy(update={"origin": origin.to_pydatetime()})
    prepared = workflow.prepare(params)
    item = prepared[0]
    assert pd.Timestamp(item["timestamps"][-1]) == last_observed
    assert pd.Timestamp(item["future"][0]) == origin + pd.Timedelta(minutes=30)
    assert item["gap_steps"] == 8
    assert item["metadata"]["data_alignment"]["synthetic_observations"] is False
    assert item["observations"] == [None] * 48
    assert len(workflow.predict_prepared(prepared)[0]) == 48
    assert station.model.steps == 56


def test_legacy_model_inputs_remain_compatible(station):
    legacy = {"target": [1., 2., 3.], "past_covariates": {"humidity": [40., 41., 42.]},
              "future": ["2025-01-03T00:30:00+00:00", "2025-01-03T01:00:00+00:00"]}
    result = station.workflow.predict_prepared([legacy])
    assert len(result[0]) == 2
    np.testing.assert_array_equal(station.model.inputs[0]["target"], legacy["target"])
    np.testing.assert_array_equal(station.model.inputs[0]["past_covariates"]["humidity"], legacy["past_covariates"]["humidity"])
