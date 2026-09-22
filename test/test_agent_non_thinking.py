"""Verify non-thinking options at both agent entry points, without remote calls."""
import json
import importlib.util
import asyncio
from pathlib import Path
from types import SimpleNamespace

import httpx
import pytest
import yaml
from langchain_openai import ChatOpenAI

from infra.non_thinking import non_thinking_options
from scientific_agents.forecast import dialogue


# Load this factory independently of agents.__init__, which eagerly imports the
# unrelated main agent and its optional deepagents dependency.
spec = importlib.util.spec_from_file_location("tested_cross_dag_factory",
    Path(__file__).resolve().parents[1] / "agents/cross_dag/factory.py")
factory = importlib.util.module_from_spec(spec)
spec.loader.exec_module(factory)


PROFILES = [
    ("relayrouter", "qwen3.8-flash", "https://api.relayrouter.ai/v1", {"extra_body": {"enable_thinking": False}}),
    ("openai", "Qwen/Qwen3.8-Flash", "https://api.relayrouter.ai/v1", {"extra_body": {"enable_thinking": False}}),
    ("dashscope", "qwen3.8-flash", "https://api.relayrouter.ai/v1", {"extra_body": {"enable_thinking": False}}),
    ("relayrouter", "qwen3.8-flash", "https://relay.example/v1", {"extra_body": {"enable_thinking": False}}),
    ("dashscope", "qwen3.8-flash", "https://dashscope.aliyuncs.com/compatible-mode/v1", {"enable_thinking": False}),
    ("relayrouter", "qwen3.8-flash", "https://dashscope-intl.aliyuncs.com/compatible-mode/v1", {"enable_thinking": False}),
    ("openai", "qwen3.8-flash", "https://workspace.ap-southeast-1.maas.aliyuncs.com/compatible-mode/v1", {"enable_thinking": False}),
    ("relayrouter", "deepseek-v4.1-flash", "https://api.relayrouter.ai/v1", {"thinking": {"type": "disabled"}}),
    ("deepseek", "deepseek-flash", "https://api.deepseek.com/v1", {"thinking": {"type": "disabled"}}),
    ("relay", "deepseek-ai/DeepSeek-V3.2", "https://relay.invalid/v1", {"thinking": {"type": "disabled"}}),
    ("dashscope", "deepseek-v4.1-flash", "https://dashscope.aliyuncs.com/compatible-mode/v1", {"enable_thinking": False}),
    ("custom", "deepseek-v4-flash", "https://dashscope-intl.aliyuncs.com/compatible-mode/v1", {"enable_thinking": False}),
    ("relay", "Qwen/Qwen3.5-Plus", "https://relay.invalid/v1", {"enable_thinking": False}),
    ("openai", "glm-4.7", "https://open.bigmodel.cn/api/paas/v4", {"thinking": {"type": "disabled"}}),
    ("moonshot", "kimi-k2.5", "https://api.moonshot.ai/v1", {"thinking": {"type": "disabled"}}),
    ("openrouter", "qwen/qwen3-32b", "https://openrouter.ai/api/v1", {"reasoning": {"enabled": False}}),
    ("custom", "deepseek/deepseek-v4.1-flash", "https://openrouter.ai/api/v1", {"reasoning": {"enabled": False}}),
    ("openai", "gpt-4o", "https://api.openai.com/v1", {}),
]


@pytest.mark.parametrize("provider,model,url,expected", PROFILES)
def test_protocol_mapping(provider, model, url, expected):
    options = non_thinking_options(provider=provider, model=model, base_url=url)
    assert options == ({"extra_body": expected} if expected else {})


@pytest.mark.parametrize("model", ["deepseek-r1", "deepseek-ai/DeepSeek-R1-0528", "qwq-32b",
                                  "Qwen/Qwen3-235B-A22B-Thinking-2507", "kimi-k2-thinking",
                                  "kimi-k2.7-code", "kimi-k3", "glm-5.3-flash"])
def test_thinking_only_variants_are_not_silently_treated_as_disabled(model):
    with pytest.raises(ValueError, match="不支持关闭思考"):
        non_thinking_options(provider="relay", model=model, base_url="https://relay.invalid/v1")


def test_unknown_model_does_not_get_invented_parameters(caplog):
    assert non_thinking_options(provider="custom", model="unknown-model", base_url="https://relay.invalid/v1") == {}
    assert "未发送关闭参数" in caplog.text


@pytest.mark.parametrize("entry", ["forecast", "cross_dag"])
@pytest.mark.parametrize("provider,model,url,expected", PROFILES)
def test_actual_agent_request_payloads(tmp_path, monkeypatch, entry, provider, model, url, expected):
    monkeypatch.setenv("TEST_AGENT_LLM_KEY", "test-key")
    monkeypatch.setenv("FORECAST_DIALOGUE", "llm")
    requests = []

    def respond(request):
        requests.append(json.loads(request.content))
        return httpx.Response(200, json={
            "id": "test", "object": "chat.completion", "created": 0, "model": model,
            "choices": [{"index": 0, "finish_reason": "stop", "message": {
                "role": "assistant", "content": '{"action":"predict","horizon_hours":72}'}}],
        })

    with httpx.Client(transport=httpx.MockTransport(respond)) as client:
        def constructor(**kwargs):
            return ChatOpenAI(http_client=client, **kwargs)

        if entry == "forecast":
            folder = tmp_path / "config"
            folder.mkdir()
            (folder / "llm.yaml").write_text(yaml.safe_dump({
                "llm": {"provider": provider, "model": model},
                "providers": {provider: {"base_url": url, "api_key_env": "TEST_AGENT_LLM_KEY"}},
            }), encoding="utf-8")
            monkeypatch.setattr(dialogue, "PROJECT_ROOT", tmp_path)
            monkeypatch.setattr("langchain_openai.ChatOpenAI", constructor)
            interpreter = dialogue.create_interpreter()
            assert interpreter.parse("Forecast three days", {}, []).horizon_hours == 72
            assert interpreter.model.request_timeout == 60
            assert interpreter.model.max_retries == 0
        else:
            settings = SimpleNamespace(llm=SimpleNamespace(provider=provider, model="unused-default"),
                providers={provider: SimpleNamespace(base_url=url, api_key_env="TEST_AGENT_LLM_KEY")})
            # The effective cross_dag model override determines the protocol.
            config = SimpleNamespace(llm_model=model, llm_timeout_seconds=120,
                                     llm_json_mode=True, llm_enable_thinking=True)
            monkeypatch.setattr(factory, "get_settings", lambda: settings)
            monkeypatch.setattr("runtime.cross_dag.config.get_cross_dc_config", lambda: config)
            monkeypatch.setattr(factory, "ChatOpenAI", constructor)
            llm = factory.CrossDagLLMFactory.create_llm()
            llm.invoke("Return JSON")
            assert llm.request_timeout == 120
            assert llm.max_retries == 2
            assert config.llm_enable_thinking is True  # No mutation of shared settings.
            assert settings.llm.model == "unused-default"
        body = requests[0]
        assert {key: body[key] for key in ("thinking", "enable_thinking", "reasoning", "extra_body") if key in body} == expected
        assert body["response_format"] == {"type": "json_object"}
        assert body["model"] == model
        assert body["temperature"] == 0


@pytest.mark.parametrize("provider,model,url,expected", [
    ("relayrouter", "qwen3.8-flash", "https://api.relayrouter.ai/v1", {"extra_body": {"enable_thinking": False}}),
    ("dashscope", "qwen3.8-flash", "https://dashscope.aliyuncs.com/compatible-mode/v1", {"enable_thinking": False}),
    ("relayrouter", "deepseek-v4.1-flash", "https://api.relayrouter.ai/v1", {"thinking": {"type": "disabled"}}),
])
def test_forecast_fact_selection_and_async_analysis_keep_non_thinking(provider, model, url, expected):
    requests = []

    def respond(request):
        requests.append(json.loads(request.content))
        note = {"text": "Inspect the forecast.", "fact_ids": ["fact"]}
        content = ({"fact_ids": ["fact"]} if len(requests) == 1 else
                   {"overview": [note], "evidence": [note], "limitations": [note]})
        return httpx.Response(200, json={
            "id": "test", "object": "chat.completion", "created": 0, "model": model,
            "choices": [{"index": 0, "finish_reason": "stop", "message": {
                "role": "assistant", "content": json.dumps(content)}}],
        })

    async def exercise():
        transport = httpx.MockTransport(respond)
        with httpx.Client(transport=transport) as client:
            async with httpx.AsyncClient(transport=transport) as async_client:
                llm = ChatOpenAI(model=model, api_key="test-key",
                    base_url=url, http_client=client, http_async_client=async_client,
                    **non_thinking_options(provider=provider, model=model, base_url=url))
                interpreter = dialogue.LLMInterpreter(llm)
                assert interpreter.select_facts("Explain", {"fact": "Forecast completed"}) == ["fact"]
                draft = await interpreter.analyze_warning({"facts": {"fact": "Forecast completed"}})
                assert draft.overview[0].fact_ids == ["fact"]

    asyncio.run(exercise())
    assert len(requests) == 2
    assert all({k: body[k] for k in ("thinking", "enable_thinking", "reasoning", "extra_body") if k in body}
               == expected for body in requests)
