"""Task-level replay never mutates the source or borrows future observations."""
import numpy as np
import pandas as pd
import pytest

from scientific_agents.forecast.feedback import ForecastError
from scientific_agents.forecast.planning import resolve_origin, OriginChoice
from scientific_agents.forecast.schema import TaskParams
from scientific_agents.forecast.ingest.campbell import CampbellProvider
from test_forecast_time_windows import workflow_for


def test_explicit_past_and_future_use_task_mode_without_changing_source(tmp_path):
    workflow, _ = workflow_for(tmp_path, 30, "2026-09-20T12:00:00+08:00", mode="current")
    params = dict(case_ids=["generic"], origin="2026-09-17T00:00:00+08:00", origin_mode="explicit", horizon_hours=72)
    now = "2026-09-20T11:19:00+08:00"
    planned = resolve_origin(params, workflow.registry, now)
    assert planned["forecast_mode"] == "historical_replay"
    assert "history_cutoff" not in planned
    bound = workflow.registry.bind(TaskParams.model_validate(planned))
    assert bound.warnings.get(bound.cases["generic"]).mode == "historical_replay"
    assert workflow.registry.warnings.get(workflow.registry.cases["generic"]).mode == "current"
    planned = resolve_origin({**params, "origin": "2026-09-21T00:00:00+08:00"}, workflow.registry, now)
    assert planned["forecast_mode"] == "current"
    assert pd.Timestamp(planned["history_cutoff"]) == pd.Timestamp(now)


def test_replay_inputs_and_station_completion_are_causal(tmp_path):
    origin = pd.Timestamp("2026-09-17T00:00:00+08:00")
    workflow, raw = workflow_for(tmp_path, 30, origin + pd.Timedelta(days=1), mode="current")
    provider = workflow.registry.source_providers["source"]
    provider.complete_history_to_origin = True
    provider.prepare_history = CampbellProvider.prepare_history
    # No observation in the six hours before replay; future truth must not fill it.
    raw.values.loc[(raw.values.index > origin - pd.Timedelta(hours=6)) & (raw.values.index <= origin)] = np.nan
    raw.values.loc[raw.values.index > origin] = 999999
    before = raw.values.copy()
    params = TaskParams(case_ids=["generic"], origin=origin, horizon_hours=24, forecast_mode="historical_replay")
    item = workflow.prepare(params)[0]
    assert item["scenario"]["mode"] == "historical_replay"
    assert pd.Timestamp(item["timestamps"][-1]) == origin.tz_convert("UTC")
    assert max(item["model_input"]["target"]) < 999999
    assert set(item["observations"]) == {999999}
    assert item["quality"]["measurement"]["filled_points"] > 0
    pd.testing.assert_series_equal(raw.values, before)
    assert workflow.registry.warnings.get(workflow.registry.cases["generic"]).mode == "current"


def test_current_staleness_offers_only_a_validated_replay_window(tmp_path):
    latest = pd.Timestamp.now(tz="UTC").floor("h") - pd.Timedelta(days=4)
    workflow, raw = workflow_for(tmp_path, 60, latest, mode="current")
    workflow._bound = True
    workflow.registry.series_info["generic"] = {"latest_observation": latest.isoformat()}
    params = TaskParams(case_ids=["generic"], origin=pd.Timestamp.now(tz="UTC"), horizon_hours=24, forecast_mode="current")
    with pytest.raises(ForecastError) as caught:
        workflow.prepare(params)
    assert caught.value.code == "data_stale"
    suggestion = caught.value.problem()["replay"]
    assert pd.Timestamp(suggestion["origin"]) + pd.Timedelta(hours=24) <= latest
    assert "回复“使用历史回放”" in str(caught.value)
    assert not hasattr(workflow.model, "inputs")  # Validation does not run TimesFM.
    assert workflow.registry.warnings.get(workflow.registry.cases["generic"]).mode == "current"
    raw.values.iloc[:-2] = np.nan
    with pytest.raises(ForecastError) as caught:
        workflow.prepare(params)
    assert "replay" not in caught.value.problem()
    assert "尚未找到通过检查" in str(caught.value)


def test_replay_without_date_or_catalogue_coverage_asks_for_date(tmp_path):
    workflow, _ = workflow_for(tmp_path, 60, "2026-09-16T00:00:00+08:00", mode="current")
    with pytest.raises(OriginChoice) as caught:
        resolve_origin(dict(case_ids=["generic"], origin_mode="replay", horizon_hours=24), workflow.registry)
    assert caught.value.interaction["field"] == "origin"


def test_legacy_replay_default_and_task_fields_remain_supported(tmp_path):
    workflow, _ = workflow_for(tmp_path, 60, "2026-09-16T00:00:00+08:00")
    date = pd.Timestamp("2026-09-15T00:00:00+08:00").to_pydatetime()
    workflow.registry.warnings.scenarios["generic"].default_replay_origin = date
    result = resolve_origin(dict(case_ids=["generic"], origin_mode="replay", horizon_hours=24), workflow.registry)
    assert pd.Timestamp(result["origin"]) == pd.Timestamp(date)
    old = TaskParams(case_ids=["generic"], origin=date, horizon_hours=24)
    assert old.forecast_mode is None
    assert workflow.prepare(old)[0]["scenario"]["mode"] == "historical_replay"


def test_explicit_input_range_excludes_outside_values_and_preserves_gap(tmp_path):
    origin = pd.Timestamp("2026-09-15T00:00:00+08:00")
    start, end = origin - pd.Timedelta(days=11), origin - pd.Timedelta(days=1)
    workflow, raw = workflow_for(tmp_path, 30, origin + pd.Timedelta(days=1), mode="current")
    raw.values.loc[(raw.values.index <= start) | (raw.values.index > end)] = 999999
    raw.values.loc[(raw.values.index > start) & (raw.values.index <= end)] = 7
    before = raw.values.copy()
    params = TaskParams(case_ids=["generic"], origin=origin, history_start=start, history_cutoff=end,
                        horizon_hours=24, history_hours=240, forecast_mode="historical_replay")
    item = workflow.prepare(params)[0]
    assert len(item["target"]) == 480
    assert set(item["target"]) == {7}
    assert pd.Timestamp(item["timestamps"][0]) == start + pd.Timedelta(minutes=30)
    assert pd.Timestamp(item["timestamps"][-1]) == end
    assert item["gap_steps"] == 48
    assert item["history_window"]["source"] == "explicit"
    assert not item["history_window"]["adjusted"]
    pd.testing.assert_series_equal(raw.values, before)


def test_station_filling_cannot_reach_before_explicit_history_start(tmp_path):
    origin = pd.Timestamp("2026-09-15T00:00:00+08:00")
    start = origin - pd.Timedelta(days=11)
    workflow, raw = workflow_for(tmp_path, 30, origin + pd.Timedelta(days=1), mode="current")
    provider = workflow.registry.source_providers["source"]
    provider.complete_history_to_origin = True
    provider.prepare_history = CampbellProvider.prepare_history
    raw.values.loc[raw.values.index <= start] = 999999
    raw.values.loc[(raw.values.index > start) & (raw.values.index <= origin)] = 7
    raw.values.loc[(raw.values.index > start) & (raw.values.index <= start + pd.Timedelta(days=1))] = np.nan
    params = TaskParams(case_ids=["generic"], origin=origin, history_start=start, history_cutoff=origin,
                        horizon_hours=24, forecast_mode="historical_replay")
    with pytest.raises(ForecastError) as caught:
        workflow.prepare(params)
    assert caught.value.code == "data_quality"
    # A trailing 7-day default would pass, but an explicit interval must not shrink.
    assert "48/528" in str(caught.value)
    raw.values.loc[(raw.values.index > start) & (raw.values.index <= start + pd.Timedelta(days=1))] = 7
    raw.values.loc[(raw.values.index > origin - pd.Timedelta(hours=6)) & (raw.values.index <= origin)] = np.nan
    item = workflow.prepare(params)[0]
    assert len(item["model_input"]["target"]) == 528
    assert set(item["model_input"]["target"]) == {7}


@pytest.mark.parametrize("minutes", [7, 30, 60])
def test_non_aligned_history_interval_uses_existing_grid(tmp_path, minutes):
    origin = pd.Timestamp("2026-09-15T00:00:00+08:00")
    start, end = origin - pd.Timedelta(hours=48, minutes=3), origin - pd.Timedelta(minutes=2)
    workflow, _ = workflow_for(tmp_path, minutes, origin, mode="historical_replay")
    params = TaskParams(case_ids=["generic"], origin=origin, history_start=start, history_cutoff=end, horizon_hours=1)
    item = workflow.prepare(params)[0]
    dates = pd.to_datetime(item["timestamps"], utc=True)
    assert (dates > start).all() and (dates <= end).all()
    assert dates[-1] == end.tz_convert("UTC").floor(f"{minutes}min")


def test_inconsistent_history_hours_and_interval_rejected(tmp_path):
    origin = pd.Timestamp("2026-09-15T00:00:00+08:00")
    workflow, _ = workflow_for(tmp_path, 30, origin)
    params = TaskParams(case_ids=["generic"], origin=origin, history_start=origin - pd.Timedelta(days=11),
                        history_hours=240, horizon_hours=24)
    with pytest.raises(ForecastError, match="不一致"):
        workflow.prepare(params)


def test_replay_with_fixed_history_starts_at_its_end_not_latest_catalogue(tmp_path):
    workflow, _ = workflow_for(tmp_path, 30, "2026-09-20T00:00:00+08:00", mode="current")
    workflow.registry.series_info["generic"] = {"latest_observation": "2026-09-20T00:00:00+08:00"}
    result = resolve_origin(dict(case_ids=["generic"], origin_mode="replay", horizon_hours=24,
        history_start="2026-09-04T00:00:00+08:00", history_cutoff="2026-09-15T00:00:00+08:00"), workflow.registry)
    assert result["origin"] == result["history_cutoff"]
    assert result["forecast_mode"] == "historical_replay"


def test_archived_auxiliary_cannot_be_relabeled_as_current(tmp_path):
    workflow, _ = workflow_for(tmp_path, 30, "2026-09-20T00:00:00+08:00", mode="current")
    registry = workflow.registry
    registry.cases["archive"] = registry.cases["generic"].model_copy(update={"id": "archive"})
    registry.providers["archive"] = registry.providers["generic"]
    registry.warnings.scenarios["archive"] = registry.warnings.scenarios["generic"].model_copy(update={"mode": "historical_replay"})
    params = dict(case_ids=["generic"], auxiliary_case_ids=["archive"], origin_mode="now", horizon_hours=24)
    with pytest.raises(OriginChoice) as caught:
        resolve_origin(params, registry)
    assert caught.value.interaction["options"][0]["id"] == "replay"
    task = TaskParams(**{**params, "origin": "2026-09-21T00:00:00+08:00", "forecast_mode": "current"})
    with pytest.raises(ForecastError, match="历史回放资料"):
        registry.bind(task)
    # Historical tasks may combine both sources without changing either registration.
    historical = registry.bind(task.model_copy(update={"forecast_mode": "historical_replay"}))
    assert historical.warnings.get(historical.cases["generic"]).mode == "historical_replay"
    assert registry.warnings.get(registry.cases["generic"]).mode == "current"


def test_known_bridge_limit_and_circular_target_are_rejected_before_reading(tmp_path):
    workflow, _ = workflow_for(tmp_path, 5, "2026-09-15T00:00:00+08:00")
    origin = pd.Timestamp("2026-09-15T00:00:00+08:00")
    with pytest.raises(ForecastError, match="1024"):
        workflow.validate(TaskParams(case_ids=["generic"], origin=origin, horizon_hours=85,
            history_cutoff=origin - pd.Timedelta(hours=1)))
    workflow.registry.cases["generic"].target.semantics = "circular_degrees"
    with pytest.raises(ForecastError, match="环形角度"):
        workflow.validate(TaskParams(case_ids=["generic"], origin=origin, horizon_hours=1))


def test_automatic_history_respects_capacity_without_changing_explicit_history(tmp_path):
    from scientific_agents.forecast.planning import history_steps
    workflow, _ = workflow_for(tmp_path, 5, "2026-09-15T00:00:00+08:00")
    workflow.settings.history_multiplier = 16
    params = TaskParams(case_ids=["generic"], origin="2026-09-15T00:00:00+08:00", horizon_hours=85)
    assert history_steps(params, workflow.registry, "generic")[0] == 15360
    with pytest.raises(ForecastError, match="最大长度"):
        history_steps(params.model_copy(update={"history_hours": 1300}), workflow.registry, "generic")


@pytest.mark.parametrize("mode", ["current", "historical_replay"])
def test_future_observations_cannot_be_requested_as_history(tmp_path, mode):
    future = pd.Timestamp.now(tz="UTC") + pd.Timedelta(days=2)
    workflow, _ = workflow_for(tmp_path, 30, future)
    with pytest.raises(ForecastError, match="不能晚于当前时刻"):
        workflow.validate(TaskParams(case_ids=["generic"], origin=future, horizon_hours=24, forecast_mode=mode))


@pytest.mark.parametrize("serialization", ["legacy", "nullable"])
def test_old_task_fingerprint_resumes_but_changed_parameters_do_not(tmp_path, monkeypatch, serialization):
    import json
    import logging
    from hashlib import sha256
    from piflow_engine.cn.piflow.core import stop_job
    monkeypatch.setattr(stop_job, "get_logger", lambda _: logging.getLogger(__name__))
    workflow, raw = workflow_for(tmp_path, 30, "2026-09-15T00:00:00+08:00")
    params = TaskParams(case_ids=["generic"], origin="2026-09-15T00:00:00+08:00", horizon_hours=24)
    first_result = workflow.run("resume-old", params, defer_report=True)
    # Reproduce the stored identity emitted before the time fields existed / when they were null.
    fields = {"analysis_context": True, "target": {"description", "aliases"},
              "covariates": {"__all__": {"description", "aliases"}}}
    settings = workflow.settings.model_dump_json(exclude={"execution": True,
        "sources": {"__all__": {"cases": {"__all__": fields}}}})
    excluded = {"history_cutoff", "history_start", "forecast_mode"} if serialization == "legacy" else {"history_cutoff"}
    model_identity = {"id": "test-only", "revision": None, "files_sha256": None}
    fingerprint = sha256((params.model_dump_json(exclude=excluded) + settings + json.dumps(model_identity, sort_keys=True)).encode()).hexdigest()
    path = tmp_path / "runs" / "resume-old" / "identity.json"
    path.write_text(json.dumps({"fingerprint": fingerprint}), encoding="utf-8")
    def fail(*_):
        raise AssertionError("Saved inputs and predictions must be reused")
    workflow.model.predict = fail
    workflow.registry.providers["generic"].read = fail
    restored = workflow.run("resume-old", params, defer_report=True)
    assert restored.series[0].predictions == first_result.series[0].predictions
    with pytest.raises(ValueError, match="配置版本已变化"):
        workflow.run("resume-old", params.model_copy(update={"history_start": pd.Timestamp(params.origin) - pd.Timedelta(days=7)}), defer_report=True)
