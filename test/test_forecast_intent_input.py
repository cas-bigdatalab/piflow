"""Intent input projection must preserve identity and conversation semantics."""
from copy import deepcopy
import json

import pytest

from scientific_agents.forecast.dialogue import LLMInterpreter
from scientific_agents.forecast.schema import Intent
from langchain_core.exceptions import OutputParserException
from langchain_core.output_parsers import PydanticOutputParser


class ReplyModel:
    """Use the real schema parser without any provider/network calls."""
    def __init__(self, replies):
        self.replies, self.calls = iter(replies), []

    def with_structured_output(self, schema, method):
        return self

    def invoke(self, messages):
        self.calls.append(messages)
        reply = next(self.replies)
        if isinstance(reply, Exception):
            raise reply
        return PydanticOutputParser(pydantic_object=Intent).parse(reply)


class CaptureModel:
    def __init__(self):
        self.messages = None

    def with_structured_output(self, schema, method):
        assert method == "json_mode"
        return self

    def invoke(self, messages):
        self.messages = messages
        return Intent(action="clarify")


def case(index, station="north", **changes):
    return {"id": f"case-{index}", "label": f"{station} station variable {index}",
            "source_id": "network", "source_name": "Observation network",
            "station_id": station, "area": station, "aliases": [f"{station} station"],
            "location": {"name": station, "address": f"{station} district", "latitude": 30, "longitude": 100},
            "variable": f"variable-{index}", "variable_aliases": [f"metric {index}"],
            "unit": "mm", "description": "Past six-hour accumulation, not an instantaneous rate",
            "hazard_type": "rainfall", "hazard_aliases": ["heavy rain"], "mode": "current",
            "covariates": ["wind"], "analysis_context": {"domain": "weather", "subject": station,
                "objective": "monitor changes", "background": "report-only background", "references": []},
            "series_status": {"row_count": 12345}, "data_status": {"last_scan": "2026-09-22"},
            "frequency_minutes": 30, "context_steps": 336, "horizons_hours": [24, 48, 72], **changes}


def capture(cases, state=None, message="预测未来三天"):
    model = CaptureModel()
    LLMInterpreter(model).parse(message, state or {}, cases)
    return model.messages, json.loads(model.messages[1][1])


def test_all_cases_and_semantic_fields_survive_without_mutating_registry():
    cases = [case(i) for i in range(30)]
    before = deepcopy(cases)
    _, context = capture(cases)
    assert cases == before
    assert len(context["cases"]) == 30  # No Top-K truncation.
    assert len(context["sites"]) == 1
    sites = {s["site_ref"]: s for s in context["sites"]}
    for original, compact in zip(cases, context["cases"]):
        site = sites[compact["site_ref"]]
        for key in ("id", "label", "variable", "variable_aliases", "description", "unit",
                    "hazard_type", "hazard_aliases", "mode", "covariates"):
            assert compact[key] == original[key]
        for key in ("source_id", "source_name", "station_id", "area", "aliases"):
            assert site[key] == original[key]
        assert site["location"] == {k: original["location"][k] for k in ("name", "address")}
        assert compact["analysis_context"] == {k: original["analysis_context"][k] for k in ("domain", "subject", "objective")}
        assert not ({"data_status", "series_status", "context_steps", "frequency_minutes"} & compact.keys())
    old = [{**c, "analysis_context": {k: v for k, v in c["analysis_context"].items()
                                    if k in {"domain", "subject", "objective"}}} for c in cases]
    new_size = len(json.dumps({k: context[k] for k in ("sites", "cases")}, ensure_ascii=False, separators=(",", ":")))
    assert new_size < len(json.dumps({"cases": old}, ensure_ascii=False)) * .75


@pytest.mark.parametrize("changes", [
    {"station_id": "south", "area": "south"},
    {"location": {"name": "Other site", "address": "Another district"}},
    {"aliases": ["A different area alias"]},
    {"source_id": "another-network"},
])
def test_distinct_sites_are_not_merged(changes):
    _, context = capture([case(1), case(2, **changes)])
    assert len(context["sites"]) == 2
    assert context["cases"][0]["site_ref"] != context["cases"][1]["site_ref"]


def test_followup_context_and_full_output_contract_are_preserved():
    state = {"params": {"case_ids": ["case-1"], "horizon_hours": 72,
                        "history_start": "2026-09-04T00:00:00+08:00", "history_cutoff": "2026-09-15T00:00:00+08:00"},
             "scope": {"requested_area": "north", "requested_variable": "rain"},
             "analysis_context": {"background": "User constraints must not be truncated" * 100},
             "history": [{"role": "user" if i % 2 == 0 else "assistant", "content": f"turn {i}"} for i in range(16)],
             "response": {"interaction": {"field": "case_ids", "prompt": "Which station?",
                                            "options": [{"id": "case-1"}, {"id": "case-2"}]}},
             "task_catalog": [{"run_id": "fc-old", "created_at": "2026-09-20T10:00:00Z",
                               "params": {"case_ids": ["case-1"], "horizon_hours": 24}}],
             "task_count": 21, "runs": [f"run-{i}" for i in range(10)]}
    before = deepcopy(state)
    messages, context = capture([case(1)], state, "还是这个站，改成五小时")
    assert state == before
    for key, original in (("confirmed_parameters", "params"), ("requested_scope", "scope"),
                          ("analysis_context", "analysis_context"), ("task_catalog", "task_catalog"), ("task_count", "task_count")):
        assert context[key] == state[original]
    assert context["pending_interaction"] == state["response"]["interaction"]
    assert context["recent_messages"] == state["history"][-12:]
    assert context["recent_run_ids"] == state["runs"][-6:]
    assert messages[-1] == ("human", "还是这个站，改成五小时")
    assert json.loads(messages[0][1].split("只输出符合以下JSON Schema的JSON对象：", 1)[1]) == Intent.model_json_schema()


def test_empty_catalog_and_explicit_json_still_work():
    _, context = capture([])
    assert context["cases"] == context["sites"] == []
    model = CaptureModel()
    intent = LLMInterpreter(model).parse('{"action":"predict","horizon_hours":5}', {}, [])
    assert intent.horizon_hours == 5
    assert model.messages is None


@pytest.mark.parametrize("bad_reply", ['not json', '{"run_ids":null}', '{"action":"forecast"}',
                                      '{"forecast_mode":"current"}', '{"requested_variable":["a","b"]}'])
def test_format_error_gets_one_schema_checked_retry(bad_reply, caplog):
    model = ReplyModel([bad_reply, '{"action":"predict","requested_variable":"soil moisture","horizon_hours":168}'])
    state = {"params": {"case_ids": ["old"]}, "history": [{"role": "user", "content": "old message"}]}
    before = deepcopy(state)
    result = LLMInterpreter(model).parse("predict next 7 days", state, [])
    assert result.horizon_hours == 168
    assert len(model.calls) == 2
    assert model.calls[1][:-1] == model.calls[0]
    assert state == before
    assert "Forecast intent format retry" in caplog.text


def test_second_invalid_output_is_not_silently_coerced_and_logs_no_values(caplog):
    secret = "PRIVATE_USER_VALUE"
    model = ReplyModel([json.dumps({secret: secret}), json.dumps({"action": secret})])
    with pytest.raises(OutputParserException):
        LLMInterpreter(model).parse("request", {}, [])
    assert len(model.calls) == 2
    assert secret not in caplog.text
    assert secret not in model.calls[1][-1][1]


@pytest.mark.parametrize("kind", ["timeout", "authentication"])
def test_network_and_auth_failures_do_not_trigger_format_retry(kind):
    import httpx
    from openai import APITimeoutError, AuthenticationError
    request = httpx.Request("POST", "https://provider.invalid/v1/chat/completions")
    error = (APITimeoutError(request=request) if kind == "timeout" else
             AuthenticationError("invalid key", response=httpx.Response(401, request=request), body=None))
    model = ReplyModel([error])
    with pytest.raises(type(error)):
        LLMInterpreter(model).parse("request", {}, [])
    assert len(model.calls) == 1


def test_repeated_parse_failure_preserves_confirmed_conversation():
    from test_forecast_conversation_matching import build_agent, first
    agent = build_agent([("rain", "降水"), ("temperature", "气温")])
    previous = first(agent)
    agent.interpreter = LLMInterpreter(ReplyModel(['{"run_ids":null}', '{"run_ids":null}']))
    state = {**previous, "session": "test", "turn_id": "bad-turn", "message": "改成气温"}
    result = agent._advance({**state, **agent._understand(state)})
    for key in ("params", "scope", "confirmed_selection"):
        assert result[key] == previous[key]
    assert result["response"]["error"]
    assert len(agent.submissions) == 1
