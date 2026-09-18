"""Exercise actual turn merging without model calls, filesystem stores or predictions."""
import json
from copy import deepcopy
from types import SimpleNamespace

import pytest

from scientific_agents.forecast.config import Case, Settings, Source, Variable
from scientific_agents.forecast.providers import Registry
from scientific_agents.forecast.runtime import ForecastAgent
from scientific_agents.forecast.schema import Intent


@pytest.fixture
def agent():
    cases, scenarios = [], []
    for site, area in [("ST001", "示例市南部观测站"), ("ST002", "示例市北部观测站")]:
        for variable, alias in [("rain", "降水"), ("temperature", "气温")]:
            case = Case(id=f"{site}-{variable}", label=f"{area} · {alias}", station_id=site,
                        target=Variable(name=variable, unit="unit", aliases=[alias]))
            cases.append(case)
            scenarios.append(dict(case_id=case.id, version="test", area=area,
                hazard_type="rainfall" if variable == "rain" else "unspecified", mode="current", use_standard=False))
    source = Source(id="network", kind="memory", display_name="示例观测网", cases=cases)
    settings = Settings(sources=[source], warning_scenarios=scenarios)
    registry = Registry(settings, providers={"network": SimpleNamespace()})
    instance = ForecastAgent.__new__(ForecastAgent)
    instance.workflow = SimpleNamespace(settings=settings, registry=registry, validate=lambda _: None)
    instance.store = SimpleNamespace(list_tasks=lambda _: [], task=lambda *_: None)
    instance.submissions = []
    instance.submit = lambda *args: instance.submissions.append(args)
    instance.task_history = SimpleNamespace(answer=lambda *_: None, list=lambda _: [])
    instance.interpreter = SimpleNamespace(parse=lambda *_: Intent())
    return instance


def advance(agent, previous=None, message="预测", **intent):
    state = {**(previous or {}), "session": "test", "turn_id": f"turn{len(agent.submissions)}",
             "message": message, "intent": Intent(**intent).model_dump(), "case_selection": False}
    return agent._advance(state)


def first(agent, **extra):
    return advance(agent, requested_area="示例市南部", requested_variable="降水", horizon_hours=72, **extra)


def confirm(agent, state, message="1"):
    state = {**state, "message": message, "session": "test", "turn_id": "confirm"}
    return agent._advance({**state, **agent._understand(state)})


def test_followup_changes_variable_and_preserves_site_and_duration(agent):
    one = first(agent, requested_hazard="rainfall")
    two = advance(agent, one, message="改成气温", requested_variable="temperature")
    assert two["params"]["case_ids"] == ["ST001-temperature"]
    assert two["params"]["horizon_hours"] == 72
    assert "requested_hazard" not in two["scope"]
    three = advance(agent, two, horizon_hours=5)
    assert three["params"]["case_ids"] == ["ST001-temperature"]
    assert three["params"]["horizon_hours"] == 5
    assert len(agent.submissions) == 3


def test_model_repeating_old_case_id_cannot_block_new_variable(agent):
    one = first(agent)
    two = advance(agent, one, requested_variable="temperature", case_ids=["ST001-rain"])
    assert two["params"]["case_ids"] == ["ST001-temperature"]
    assert len(agent.submissions) == 2


def test_new_site_preserves_variable(agent):
    two = advance(agent, first(agent), requested_area="示例市北部")
    assert two["params"]["case_ids"] == ["ST002-rain"]


def test_pending_correction_can_change_variable_and_duration_in_chinese(agent):
    pending = advance(agent, requested_area="示例南部", horizon_hours=72)
    assert pending["pending_match"] and not agent.submissions
    assert len(pending["pending_match"]["options"]) == 2
    result = advance(agent, pending, message="改成预测气温", requested_variable="temperature", horizon_hours=5)
    assert result["params"]["case_ids"] == ["ST001-temperature"]
    assert result["params"]["horizon_hours"] == 5
    assert result["pending_match"] is None
    assert len(agent.submissions) == 1


def test_unique_variable_candidate_automatically_uses_registered_variable(agent):
    result = advance(agent, requested_area="示例市南部", requested_variable="temperatur", horizon_hours=24)
    assert result["pending_match"] is None
    assert result["response"]["interaction"] is None
    assert result["scope"]["requested_variable"] == "temperature"
    assert result["params"]["case_ids"] == ["ST001-temperature"]
    assert len(agent.submissions) == 1


def test_unique_place_candidate_starts_and_followup_inherits_canonical_site(agent):
    result = advance(agent, requested_area="示例南部", requested_variable="rain", horizon_hours=72)
    assert result["params"]["case_ids"] == ["ST001-rain"]
    assert result["scope"]["requested_area"] == "示例市南部观测站"
    assert result["response"]["interaction"] is None
    assert "已匹配：示例市南部观测站 · 降水" in result["response"]["content"]
    assert len(agent.submissions) == 1
    result = advance(agent, result, requested_variable="temperature")
    assert result["params"]["case_ids"] == ["ST001-temperature"]
    assert result["params"]["horizon_hours"] == 72
    assert len(agent.submissions) == 2


def test_multiple_similar_candidates_require_choice(agent):
    pending = advance(agent, requested_area="示例观侧网", requested_variable="rain", horizon_hours=24)
    assert len(pending["pending_match"]["options"]) == 2
    assert not agent.submissions
    result = confirm(agent, pending, "2")
    assert result["params"]["case_ids"] == ["ST002-rain"]
    assert len(agent.submissions) == 1


def test_unique_match_still_requests_missing_duration(agent):
    result = advance(agent, requested_area="示例南部", requested_variable="rain")
    assert result["params"]["case_ids"] == ["ST001-rain"]
    assert result["response"]["interaction"]["field"] == "horizon_hours"
    assert not agent.submissions


def test_unique_suggestion_does_not_override_explicit_conflicting_case(agent):
    intent = dict(requested_area="示例南部", requested_variable="rain", horizon_hours=24,
                  case_ids=["ST002-rain"])
    result = advance(agent, message=json.dumps(intent), **intent)
    assert result["response"]["error"]
    assert not agent.submissions


def test_unknown_scope_does_not_reuse_last_dataset(agent):
    one = first(agent)
    two = advance(agent, one, requested_area="北京市", requested_variable="rain")
    assert two["response"]["error"]
    assert two["params"] == one["params"]
    assert len(agent.submissions) == 1


def test_source_with_multiple_sites_prompts_for_selection(agent):
    result = advance(agent, requested_area="示例观测网", requested_variable="rain", horizon_hours=24)
    assert result["response"]["interaction"]["field"] == "case_ids"
    assert len(result["response"]["interaction"]["options"]) == 2
    assert not agent.submissions


def test_model_cannot_silently_choose_one_site_from_ambiguous_source(agent):
    result = advance(agent, requested_area="示例观测网", requested_variable="rain", horizon_hours=24,
                     case_ids=["ST001-rain"])
    assert result["response"]["interaction"]["field"] == "case_ids"
    assert len(result["response"]["interaction"]["options"]) == 2
    assert not agent.submissions
    confirmed = confirm(agent, result, message="2")
    assert confirmed["params"]["case_ids"] == ["ST002-rain"]
    assert len(agent.submissions) == 1


def test_explicit_case_selection_stays_supported_and_constraints_are_checked(agent):
    one = first(agent)
    payload = dict(case_ids=["ST002-temperature"])
    two = advance(agent, one, message=json.dumps(payload), **payload)
    assert two["params"]["case_ids"] == ["ST002-temperature"]
    three = advance(agent, two, requested_variable="rain")
    assert three["params"]["case_ids"] == ["ST002-rain"]
    bad = dict(case_ids=["ST001-rain"], requested_area="北京市")
    result = advance(agent, three, message=json.dumps(bad), **bad)
    assert result["response"]["error"]
    assert len(agent.submissions) == 3


def test_missing_risk_capability_is_explained_but_target_can_be_forecast(agent):
    result = advance(agent, requested_area="示例市南部", requested_variable="temperature",
                     requested_hazard="unknown_risk", horizon_hours=24)
    assert len(agent.submissions) == 1
    assert "未登记所请求的风险类型" in result["response"]["content"]
    assert result["scope"]["requested_hazard"] == "unknown_risk"
    cleared = advance(agent, result, requested_hazard="")
    assert "requested_hazard" not in cleared["scope"]


def test_input_state_is_not_mutated(agent):
    one = first(agent)
    before = deepcopy(one)
    advance(agent, one, requested_variable="temperature")
    assert one == before


def test_explicit_named_selection_can_switch_site_without_copying_old_scope(agent):
    one = first(agent)
    two = advance(agent, one, message="选择ST002-temperature", case_ids=["ST002-temperature"])
    assert two["params"]["case_ids"] == ["ST002-temperature"]
    assert len(agent.submissions) == 2
