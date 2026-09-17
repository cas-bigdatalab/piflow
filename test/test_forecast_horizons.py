"""One duration policy for dialogue, configured/discovered sources and execution."""
from unittest.mock import patch

import pandas as pd
import pytest
from pydantic import ValidationError

from scientific_agents.forecast.config import Settings, load_settings
from scientific_agents.forecast.dialogue import ExplicitInterpreter
from scientific_agents.forecast.feedback import ForecastError
from scientific_agents.forecast.planning import resolve_origin
from scientific_agents.forecast.runtime import ForecastAgent
from scientific_agents.forecast.schema import TaskParams
from scientific_agents.forecast.warning.registry import WarningRegistry
from test_forecast_time_windows import workflow_for


@pytest.mark.parametrize("invalid", [0, -1, 1.5, True])
def test_maximum_requires_positive_integer(invalid):
    with pytest.raises(ValidationError):
        Settings(sources=[], max_horizon_hours=invalid)


def test_global_maximum_replaces_legacy_whitelist():
    registry = WarningRegistry(Settings(sources=[], max_horizon_hours=12, horizons_hours=[24, 48, 72]))
    assert registry.allowed_hours([]) == list(range(1, 13))
    registry.validate_hours(5, [])
    with pytest.raises(ForecastError, match="1～12"):
        registry.validate_hours(24, [])


@pytest.mark.parametrize("frequency", [30, 60])
@pytest.mark.parametrize("hours", [1, 5, 36, 168])
@pytest.mark.parametrize("mode", ["current", "historical_replay"])
def test_hourly_and_seven_day_requests_keep_source_grid(tmp_path, frequency, hours, mode):
    origin = pd.Timestamp.now(tz="UTC").floor("h")
    workflow, _ = workflow_for(tmp_path, frequency, origin, mode=mode)
    params = TaskParams(case_ids=["generic"], origin=origin, horizon_hours=hours)
    item = workflow.prepare(params)[0]
    expected = pd.date_range(start=origin + pd.Timedelta(minutes=frequency), periods=hours * 60 // frequency,
                             freq=f"{frequency}min")
    assert pd.to_datetime(item["future"], utc=True).tolist() == expected.tolist()
    assert item["frequency_minutes"] == frequency


def test_workflow_rejects_eight_days_before_preparing_data(tmp_path):
    origin = pd.Timestamp("2026-09-18T00:00:00Z")
    workflow, _ = workflow_for(tmp_path, 30, origin)
    with pytest.raises(ForecastError, match="1～168"):
        workflow.validate(TaskParams(case_ids=["generic"], origin=origin, horizon_hours=192))


def test_fine_sampling_and_multiple_targets_keep_model_limit(tmp_path):
    workflow, _ = workflow_for(tmp_path, 30, "2026-09-18T00:00:00Z")
    warnings = workflow.registry.warnings
    warnings.scenarios["fine"] = warnings.scenarios["generic"].model_copy(update={"frequency_minutes": 5})
    assert warnings.allowed_hours(["generic"])[-1] == 168
    assert warnings.allowed_hours(["generic", "fine"])[-1] == 85
    with pytest.raises(ForecastError, match="1024"):
        warnings.validate_hours(86, ["generic", "fine"])


def test_bridge_still_consumes_model_prediction_budget(tmp_path):
    origin = pd.Timestamp("2026-09-18T00:00:00Z")
    workflow, _ = workflow_for(tmp_path, 5, origin)
    params = TaskParams(case_ids=["generic"], origin=origin, horizon_hours=85,
                        history_cutoff=origin - pd.Timedelta(hours=1))
    with pytest.raises(ForecastError, match="数据延迟加请求时长"):
        workflow.prepare(params)


def test_registered_and_discovered_cases_share_policy(tmp_path):
    workflow, _ = workflow_for(tmp_path, 30, "2026-09-18T00:00:00Z")
    workflow.settings.warning_scenarios[0].horizons_hours = [24, 48, 72]
    workflow.registry.refresh()
    assert workflow.registry.list_cases()[0]["horizons_hours"] == list(range(1, 169))
    source = workflow.settings.sources[0]
    source.discover = True
    case = source.cases[0].model_copy(update={"id": "discovered"})
    provider = workflow.registry.source_providers[source.id]
    provider.discover = lambda: [(case, {"frequency_minutes": 30, "mode": "historical_replay"})]
    workflow.registry.refresh()
    entry = workflow.registry.list_cases()[0]
    assert entry["id"] == "discovered"
    assert entry["horizons_hours"] == list(range(1, 169))
    assert entry["frequency_minutes"] == 30


@pytest.mark.parametrize("message,hours,mode", [
    ("预测未来5小时", 5, "now"), ("预测未来36小时", 36, "now"),
    ("预测未来7天", 168, "tomorrow"), ("从现在开始预测3天", 72, "now")])
def test_existing_language_conversion_and_start_rules(tmp_path, message, hours, mode):
    interpreter = ExplicitInterpreter()
    intent = interpreter.parse(message, {}, [])
    assert (intent.horizon_hours, intent.origin_mode) == (hours, mode)
    workflow, _ = workflow_for(tmp_path, 30, pd.Timestamp.now(tz="UTC"), mode="current")
    resolved = resolve_origin({"case_ids": ["generic"], "horizon_hours": hours, "origin_mode": mode}, workflow.registry)
    assert resolved["horizon_hours"] == hours
    if mode == "tomorrow":
        assert pd.Timestamp(resolved["origin"]).tz_convert("Asia/Shanghai").hour == 0
        assert "history_cutoff" in resolved
    else:
        assert abs((pd.Timestamp.now(tz="UTC") - pd.Timestamp(resolved["origin"])).total_seconds()) < 10


def test_dialogue_shows_shortcuts_but_accepts_other_hours(tmp_path):
    workflow, _ = workflow_for(tmp_path, 30, "2026-09-18T00:00:00Z")
    agent = object.__new__(ForecastAgent)
    agent.workflow = workflow
    response = agent._interaction({"case_ids": ["generic"]}, "turn", 1)
    assert "1～168" in response["prompt"]
    assert len(response["options"]) <= 10 and 168 in response["options"]
    assert 5 not in response["options"]
    workflow.registry.warnings.validate_hours(5, ["generic"])


@pytest.mark.parametrize("hours", [24, 48, 72])
def test_previous_three_durations_keep_identical_model_inputs(tmp_path, hours):
    origin = pd.Timestamp("2026-09-18T00:00:00Z")
    workflow, _ = workflow_for(tmp_path, 30, origin)
    params = TaskParams(case_ids=["generic"], origin=origin, horizon_hours=hours)
    bound = workflow.bind(params)
    current = bound.prepare(params)
    timing = bound.registry.warnings.timing
    with patch.object(bound.registry.warnings, "timing", side_effect=lambda case: (*timing(case)[:2], [24, 48, 72])):
        legacy = bound.prepare(params)
    assert legacy == current


def test_repository_config_has_one_duration_policy():
    settings = load_settings()
    registry = WarningRegistry(settings)
    assert settings.max_horizon_hours == 168
    assert all(s.horizons_hours is None for s in settings.warning_scenarios)
    for source in settings.sources:
        for case in source.cases:
            assert registry.timing(case.id)[2] == list(range(1, 169))
