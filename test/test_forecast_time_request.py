"""Dates in the user's request take precedence over LLM defaults and old turns."""
import pytest
import pandas as pd

from scientific_agents.forecast.feedback import ForecastError
from scientific_agents.forecast.time_request import parse_time_request

NOW = "2026-09-20T11:19:00+08:00"


@pytest.mark.parametrize("message,start,hours", [
    ("我想预测青海西宁共和县9月16号之后未来三天的气温变化", "2026-09-17T00:00:00+08:00", 72),
    ("我想预测青海西宁共和县9月17号的气温变化", "2026-09-17T00:00:00+08:00", 24),
    ("从9月16号开始预测三天", "2026-09-16T00:00:00+08:00", 72),
    ("预测九月十七日气温", "2026-09-17T00:00:00+08:00", 24),
    ("预测2024年2月29日降水", "2024-02-29T00:00:00+08:00", 24),
    ("预测12月31日之后两天", "2027-01-01T00:00:00+08:00", 48),
    ("从9月17日16点30分开始预测5个小时", "2026-09-17T16:30:00+08:00", 5),
    ("从2026-09-17T10:00:00+08:00开始预测5小时", "2026-09-17T10:00:00+08:00", 5),
    ("预测昨天的气温", "2026-09-19T00:00:00+08:00", 24),
    ("预测未来三天，从9月17号开始，参考过去7天", "2026-09-17T00:00:00+08:00", 72),
    ("预测9月17号气温，参考过去7天", "2026-09-17T00:00:00+08:00", 24),
    ("从2026-09-17T00:00:00Z开始预测5小时", "2026-09-17T00:00:00+00:00", 5),
])
def test_explicit_dates(message, start, hours):
    parsed = parse_time_request(message, NOW)
    assert pd.Timestamp(parsed["origin"]) == pd.Timestamp(start)
    assert parsed["origin_mode"] == "explicit"
    assert parsed["horizon_hours"] == hours


@pytest.mark.parametrize("message", ["预测9月31号", "预测13月2日", "预测2025年2月29日", "预测17号",
    "预测9月17日和9月19日", "预测9月17号25点", "预测9月17号0天", "预测2026/09/17气温"])
def test_unresolved_or_invalid_dates_never_fall_back_to_tomorrow(message):
    with pytest.raises(ForecastError) as caught:
        parse_time_request(message, NOW)
    assert caught.value.code == "invalid_time"


@pytest.mark.parametrize("message,mode,hours", [("预测未来3天", "tomorrow", 72),
    ("从现在开始未来3天", "now", 72), ("预测未来5个小时", "now", 5)])
def test_new_relative_request_discards_explicit_origin(message, mode, hours):
    assert parse_time_request(message, NOW) == dict(origin=None, origin_mode=mode, horizon_hours=hours)


def test_unmentioned_time_and_structured_requests_are_unchanged():
    assert parse_time_request("改成气温", NOW) == {}
    assert parse_time_request('{"origin":"2026-09-17T00:00:00+08:00"}', NOW) == {}


# Reuse the small in-memory conversation fixture; no external model or task worker.
from test_forecast_conversation_matching import agent, first, advance
from scientific_agents.forecast.schema import Intent
from scientific_agents.forecast.planning import resolve_origin


def turn_with_date(agent, state, message, monkeypatch):
    monkeypatch.setattr("scientific_agents.forecast.runtime.parse_time_request", lambda text: parse_time_request(text, NOW))
    monkeypatch.setattr("scientific_agents.forecast.runtime.resolve_origin", lambda params, registry: resolve_origin(params, registry, NOW))
    state = {**state, "session": "test", "message": message, "turn_id": f"time-{len(agent.submissions)}"}
    parsed = agent._understand(state)
    return agent._advance({**state, **parsed})


def test_repeated_exact_user_dates_override_incorrect_model_and_old_time(agent, monkeypatch):
    state = first(agent)
    agent.interpreter.parse = lambda *_: Intent(origin_mode="tomorrow", horizon_hours=72)
    state = turn_with_date(agent, state, "我想预测青海西宁共和县9月16号之后未来三天的气温变化", monkeypatch)
    assert state["params"]["forecast_mode"] == "historical_replay"
    assert pd.Timestamp(state["params"]["origin"]) == pd.Timestamp("2026-09-17T00:00:00+08:00")
    assert state["params"]["horizon_hours"] == 72
    assert "history_cutoff" not in state["params"]
    for _ in range(2):
        state = turn_with_date(agent, state, "我想预测青海西宁共和县9月17号的气温变化", monkeypatch)
        assert pd.Timestamp(state["params"]["origin"]) == pd.Timestamp("2026-09-17T00:00:00+08:00")
        assert state["params"]["horizon_hours"] == 24
        assert "历史回放" in state["response"]["content"]
    assert len(agent.submissions) == 4
    agent.interpreter.parse = lambda *_: Intent(origin="2026-09-17T00:00:00+08:00", horizon_hours=24)
    state = turn_with_date(agent, state, "改为预测未来5小时", monkeypatch)
    assert state["params"]["forecast_mode"] == "current"
    assert pd.Timestamp(state["params"]["origin"]) == pd.Timestamp(NOW)
    assert state["params"]["horizon_hours"] == 5


def test_invalid_date_preserves_state_without_submitting(agent, monkeypatch):
    previous = first(agent)
    result = turn_with_date(agent, previous, "预测9月31号的气温", monkeypatch)
    assert result["response"]["problem"]["code"] == "invalid_time"
    assert result["params"] == previous["params"]
    assert len(agent.submissions) == 1


def test_provider_error_is_not_reported_as_user_misunderstanding(agent, monkeypatch):
    previous = first(agent)
    def fail(*_):
        raise TimeoutError()
    agent.interpreter.parse = fail
    result = turn_with_date(agent, previous, "预测9月17号的气温", monkeypatch)
    assert result["response"]["problem"]["code"] == "intent_service_failed"
    assert result["params"] == previous["params"]
    assert len(agent.submissions) == 1


def test_date_reply_to_origin_question_does_not_require_predict_verb(agent, monkeypatch):
    state = first(agent)
    state["response"]["interaction"] = {"field": "origin", "options": []}
    agent.interpreter.parse = lambda *_: Intent(action="unsupported")
    result = turn_with_date(agent, state, "9月17号", monkeypatch)
    assert result["params"]["forecast_mode"] == "historical_replay"
    assert result["params"]["horizon_hours"] == 24
    assert pd.Timestamp(result["params"]["origin"]) == pd.Timestamp("2026-09-17T00:00:00+08:00")


def test_replay_reply_uses_the_validated_window_without_model_call(agent, monkeypatch):
    state = first(agent)
    origin = "2026-09-12T00:00:00+08:00"
    task = {"params": {**state["params"], "auxiliary_case_ids": []},
            "problem": {"replay": {"origin": origin, "horizon_hours": 72}}}
    agent.task_history.list = lambda _: [task]
    agent.task_history.summary = lambda _: {}
    def fail(*_):
        raise AssertionError("Replay confirmation must not call the LLM")
    agent.interpreter.parse = fail
    result = turn_with_date(agent, state, "使用历史回放", monkeypatch)
    assert result["params"]["forecast_mode"] == "historical_replay"
    assert pd.Timestamp(result["params"]["origin"]) == pd.Timestamp(origin)
    assert len(agent.submissions) == 2


@pytest.mark.parametrize("message", [
    "你能否基于9月4号——9月14号，来预测9月15号的湿度",
    "使用9月4日到14日的数据预测9月15日湿度",
    "预测9月15日湿度，参考9月4日～9月14日的数据",
])
def test_distinct_history_and_forecast_ranges(message):
    parsed = parse_time_request(message, NOW)
    assert parsed["history_start"] == "2026-09-04T00:00:00+08:00"
    assert parsed["history_cutoff"] == "2026-09-15T00:00:00+08:00"
    assert parsed["history_hours"] == 264
    assert parsed["origin"] == "2026-09-15T00:00:00+08:00"
    assert parsed["horizon_hours"] == 24


def test_history_and_forecast_both_have_ranges():
    parsed = parse_time_request("基于9月4日至9月14日的数据，预测9月15日至9月17日", NOW)
    assert parsed["history_hours"] == 264
    assert parsed["horizon_hours"] == 72


def test_explicit_clock_and_cross_year_history_boundaries():
    parsed = parse_time_request("基于9月4日10:00至9月14日10:30，预测9月15日", NOW)
    assert parsed["history_start"] == "2026-09-04T10:00:00+08:00"
    assert parsed["history_cutoff"] == "2026-09-14T10:30:00+08:00"
    assert parsed["history_hours"] is None
    parsed = parse_time_request("基于2025年12月25日至1月3日的数据，预测1月4日", NOW)
    assert parsed["history_cutoff"] == "2026-01-04T00:00:00+08:00"
    assert parsed["history_hours"] == 240


@pytest.mark.parametrize("message", [
    "基于9月14日至9月4日预测9月15日", "基于9月4日至9月16日预测9月15日",
    "基于9月31日至10月3日预测10月4日", "基于9月4日和9月14日预测9月15日",
])
def test_ambiguous_reversed_or_leaking_input_ranges_are_rejected(message):
    with pytest.raises(ForecastError):
        parse_time_request(message, NOW)


def test_actual_user_range_overrides_wrong_llm_length_and_persists_on_followup(agent, monkeypatch):
    state = first(agent)
    agent.interpreter.parse = lambda *_: Intent(origin_mode="tomorrow", horizon_hours=72, history_hours=240)
    result = turn_with_date(agent, state, "你能否基于9月4号——9月14号，来预测9月15号的湿度", monkeypatch)
    assert not result["response"].get("error"), result["response"]
    assert result["params"]["history_hours"] == 264
    assert result["params"]["forecast_mode"] == "historical_replay"
    assert result["params"]["history_cutoff"] == "2026-09-15T00:00:00+08:00"
    assert result["params"]["horizon_hours"] == 24
    assert "历史输入区间：2026-09-04 00:00 至 2026-09-15 00:00" in result["response"]["content"]
    agent.interpreter.parse = lambda *_: Intent(requested_variable="temperature")
    result = turn_with_date(agent, result, "改成气温", monkeypatch)
    assert result["params"]["history_start"] == "2026-09-04T00:00:00+08:00"
    assert result["params"]["history_cutoff"] == "2026-09-15T00:00:00+08:00"
    agent.interpreter.parse = lambda *_: Intent(history_mode="auto")
    result = turn_with_date(agent, result, "恢复默认历史窗口", monkeypatch)
    assert "history_start" not in result["params"]
    assert "history_cutoff" not in result["params"]
    assert "history_hours" not in result["params"]


@pytest.mark.parametrize("message,start,hours", [
    ("从昨天开始预测未来三天", "2026-09-19T00:00:00+08:00", 72),
    ("从明天10点开始预测未来5小时", "2026-09-21T10:00:00+08:00", 5),
    ("预测前天到昨天的气温", "2026-09-18T00:00:00+08:00", 48),
    ("参考过去7天预测后天的气温", "2026-09-22T00:00:00+08:00", 24),
])
def test_relative_day_is_an_explicit_anchor(message, start, hours):
    result = parse_time_request(message, NOW)
    assert result["origin"] == start
    assert result["horizon_hours"] == hours


def test_history_year_and_duration_do_not_become_forecast_defaults():
    result = parse_time_request("基于2024年9月4日至9月14日的数据预测9月15日", NOW)
    assert result["origin"] == "2024-09-15T00:00:00+08:00"
    result = parse_time_request("参考过去7天预测未来5小时", NOW)
    assert result["history_hours"] == 168
    assert result["horizon_hours"] == 5
    assert result["origin_mode"] == "now"
    with pytest.raises(ForecastError, match="大于零"):
        parse_time_request("参考过去0天预测明天", NOW)


@pytest.mark.parametrize("action,message", [
    ("compare", "比较9月15日和9月16日的预测结果"),
    ("explain", "解释昨天和前天的预测为什么不同"),
    ("report", "下载9月15日和9月16日的预测报告"),
    ("status", "9月15号的预测做完了吗"),
])
def test_result_references_do_not_parse_as_new_forecast_dates(agent, action, message):
    agent.interpreter.parse = lambda *_: Intent(action=action)
    result = agent._understand({"session": "test", "message": message})
    assert not result["parse_error"]
    assert result["intent"]["action"] == action
    assert result["intent"]["origin"] is None


def test_history_duration_overrides_wrong_model_and_clears_old_fixed_range(agent, monkeypatch):
    state = first(agent)
    state = turn_with_date(agent, state, "基于9月4日至9月14日预测9月15日", monkeypatch)
    agent.interpreter.parse = lambda *_: Intent(history_hours=24, horizon_hours=168)
    result = turn_with_date(agent, state, "参考过去7天预测未来5小时", monkeypatch)
    assert result["params"]["history_hours"] == 168
    assert "history_start" not in result["params"]
    assert result["params"]["horizon_hours"] == 5
    assert result["params"]["forecast_mode"] == "current"


def test_unknown_auxiliary_is_rejected_before_task_submission(agent):
    result = advance(agent, first(agent), message='{"auxiliary_case_ids":["missing"]}', auxiliary_case_ids=["missing"])
    assert result["response"]["problem"]["code"] == "invalid_parameters"
    assert len(agent.submissions) == 1


def test_reuse_of_old_current_task_keeps_time_but_uses_replay(agent, monkeypatch):
    state = first(agent)
    source = {"run_id": "old-run", "params": {**state["params"],
        "origin": "2026-09-15T00:00:00+08:00", "forecast_mode": "current"}}
    agent._task_for = lambda *_: source
    agent.interpreter.parse = lambda *_: Intent(action="reuse")
    result = turn_with_date(agent, state, "按之前的条件重新预测", monkeypatch)
    assert not result["response"].get("error")
    assert result["params"]["origin"] == source["params"]["origin"]
    assert result["params"]["forecast_mode"] == "historical_replay"
