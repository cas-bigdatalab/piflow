"""Exercise actual turn merging without model calls, filesystem stores or predictions."""
import json
from copy import deepcopy
from types import SimpleNamespace

import pytest

from scientific_agents.forecast.config import Case, Settings, Source, Variable
from scientific_agents.forecast.providers import Registry
from scientific_agents.forecast.runtime import ForecastAgent
from scientific_agents.forecast.schema import Intent


def build_agent(variables):
    cases, scenarios = [], []
    for site, area in [("ST001", "示例市南部观测站"), ("ST002", "示例市北部观测站")]:
        for variable, alias in variables:
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


@pytest.fixture
def agent():
    return build_agent([("rain", "降水"), ("temperature", "气温")])


@pytest.fixture
def temperature_agent():
    return build_agent([("air_temperature", "气温"), ("soil_temperature", "土壤温度")])


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


def test_exact_variable_with_short_place_starts_without_soil_choice(temperature_agent):
    result = advance(temperature_agent, requested_area="示例南部", requested_variable="air_temperature", horizon_hours=72)
    assert result["params"]["case_ids"] == ["ST001-air_temperature"]
    assert result["pending_match"] is None
    assert result["response"]["interaction"] is None
    assert len(temperature_agent.submissions) == 1
    followup = advance(temperature_agent, result, requested_variable="soil_temperature")
    assert followup["params"]["case_ids"] == ["ST001-soil_temperature"]
    assert followup["params"]["horizon_hours"] == 72
    assert len(temperature_agent.submissions) == 2


def test_similar_source_keeps_multiple_sites_but_not_other_variables(temperature_agent):
    pending = advance(temperature_agent, requested_area="示例观侧网", requested_variable="air_temperature", horizon_hours=24)
    assert {c["id"] for c in pending["pending_match"]["options"]} == {
        "ST001-air_temperature", "ST002-air_temperature"}
    assert not temperature_agent.submissions
    result = confirm(temperature_agent, pending, "2")
    assert result["params"]["case_ids"] == ["ST002-air_temperature"]
    assert len(temperature_agent.submissions) == 1


@pytest.mark.parametrize("model_ids", [["ST001-rain"], ["ST001-rain", "ST002-rain"]])
def test_all_model_selections_require_confirmation_for_ambiguous_scope(agent, model_ids):
    result = advance(agent, message="预测示例观测网的降水", requested_area="示例观测网",
                     requested_variable="rain", horizon_hours=24, case_ids=model_ids)
    assert not agent.submissions
    assert len(result["response"]["interaction"]["options"]) == 2
    assert result["confirmed_selection"] == {}
    chosen = confirm(agent, result, "2")
    assert chosen["confirmed_selection"]["case_ids"] == ["ST002-rain"]
    # Re-opened state retains the user's choice, even if the model suggests all IDs.
    restored = json.loads(json.dumps(chosen, default=str))
    followup = advance(agent, restored, message="改成未来五小时", horizon_hours=5, case_ids=model_ids)
    assert followup["params"]["case_ids"] == ["ST002-rain"]
    assert followup["response"]["interaction"] is None
    assert len(agent.submissions) == 2


def test_model_specific_channel_cannot_hide_broad_variable_request():
    agent = build_agent([(f"moisture_probe{i}", "土壤水分") for i in range(1, 4)])
    result = advance(agent, message="预测ST001未来7天的土壤水分变化", requested_area="ST001",
                     requested_variable="moisture_probe1", case_ids=["ST001-moisture_probe1"], horizon_hours=168)
    assert result["scope"]["requested_variable"] == "土壤水分"
    assert not agent.submissions
    assert len(result["response"]["interaction"]["options"]) == 3


def test_model_specific_station_cannot_hide_source_request(agent):
    result = advance(agent, message="预测示例观测网未来一天的降水", requested_area="ST001",
                     requested_variable="rain", case_ids=["ST001-rain"], horizon_hours=24)
    assert result["scope"]["requested_area"] == "示例观测网"
    assert not agent.submissions
    assert len(result["response"]["interaction"]["options"]) == 2


def test_changed_scope_reasks_and_old_state_without_proof_is_not_confirmation(agent):
    one = first(agent)
    broad = advance(agent, one, requested_area="示例观测网", case_ids=["ST001-rain"])
    assert broad["response"]["interaction"]["field"] == "case_ids"
    assert len(agent.submissions) == 1
    legacy = {**one, "scope": {"requested_area": "示例观测网", "requested_variable": "rain"}}
    legacy.pop("confirmed_selection")
    result = advance(agent, legacy, horizon_hours=5, case_ids=["ST001-rain"])
    assert result["response"]["interaction"]["field"] == "case_ids"
    assert len(agent.submissions) == 1


def test_new_ambiguous_variable_does_not_inherit_old_explicit_selection():
    agent = build_agent([("rain", "降水"), ("moisture_a", "土壤水分"), ("moisture_b", "土壤水分")])
    one = first(agent)
    result = advance(agent, one, message="土壤水分呢", requested_variable="moisture_a",
                     case_ids=["ST001-moisture_a", "ST001-moisture_b"])
    assert result["response"]["interaction"]["field"] == "case_ids"
    assert len(result["response"]["interaction"]["options"]) == 2
    assert len(agent.submissions) == 1


@pytest.mark.parametrize("targets,auxiliary", [(["ST001-rain", "ST002-rain"], []),
                                             (["ST001-rain"], ["ST001-temperature"])])
def test_manual_multiple_targets_and_auxiliary_selection_are_preserved(agent, targets, auxiliary):
    payload = dict(case_ids=targets, auxiliary_case_ids=auxiliary, horizon_hours=24)
    one = advance(agent, message=json.dumps(payload), **payload)
    assert one["params"]["case_ids"] == payload["case_ids"]
    assert agent.submissions[0][2].auxiliary_case_ids == payload["auxiliary_case_ids"]
    two = advance(agent, one, horizon_hours=5, case_ids=["ST002-temperature"])
    assert two["params"]["case_ids"] == payload["case_ids"]
    assert two["params"]["auxiliary_case_ids"] == auxiliary
    assert len(agent.submissions) == 2


def test_explicit_historical_reuse_does_not_prompt_for_dataset_again(agent):
    source = {"run_id": "old", "params": dict(case_ids=["ST001-rain", "ST002-rain"],
              origin="2025-01-01T00:00:00+08:00", horizon_hours=24)}
    agent._task_for = lambda *_: source
    result = advance(agent, action="reuse", run_ids=["old"])
    assert result["response"]["source_run_id"] == "old"
    assert result["params"]["case_ids"] == source["params"]["case_ids"]
    assert result["confirmed_selection"]["case_ids"] == source["params"]["case_ids"]
    assert len(agent.submissions) == 1


def test_selection_proof_survives_graph_checkpoint_reload():
    from langgraph.checkpoint.memory import InMemorySaver
    from langgraph.graph import StateGraph, START, END
    from scientific_agents.forecast.runtime import Conversation
    checkpointer = InMemorySaver()

    def graph(agent):
        workflow = StateGraph(Conversation)
        workflow.add_node("advance", agent._advance)
        workflow.add_edge(START, "advance")
        workflow.add_edge("advance", END)
        return workflow.compile(checkpointer=checkpointer)

    first_agent = build_agent([("rain", "降水")])
    payload = dict(case_ids=["ST001-rain", "ST002-rain"], horizon_hours=24)
    config = {"configurable": {"thread_id": "test"}}
    graph(first_agent).invoke(dict(session="test", turn_id="first", message=json.dumps(payload),
                                  intent=Intent(**payload).model_dump()), config)
    restored_agent = build_agent([("rain", "降水")])
    result = graph(restored_agent).invoke(dict(turn_id="next", message="改成五小时",
                                        intent=Intent(horizon_hours=5).model_dump()), config)
    assert result["confirmed_selection"]["case_ids"] == payload["case_ids"]
    assert result["params"]["horizon_hours"] == 5
    assert len(restored_agent.submissions) == 1
