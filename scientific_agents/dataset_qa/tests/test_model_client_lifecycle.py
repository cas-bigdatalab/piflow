"""Offline regressions for model HTTP client ownership and failed construction."""
import asyncio
from types import SimpleNamespace

import pytest

from ..dialogue import Dialogue


@pytest.fixture
def model_settings(monkeypatch):
    from infra import config_loader
    settings = SimpleNamespace(llm=SimpleNamespace(provider="test", model="qwen3.5-plus", temperature=0.2),
        providers={"test": SimpleNamespace(api_key_env="QA_LIFECYCLE_TEST_KEY",
            base_url="https://model-lifecycle.invalid/v1")})
    monkeypatch.setattr(config_loader, "get_settings", lambda: settings)
    monkeypatch.setenv("QA_LIFECYCLE_TEST_KEY", "offline-test-only")
    return settings


def test_dialogues_own_distinct_clients_and_close_does_not_poison_next_model(model_settings):
    async def run():
        first, second, third = Dialogue(), Dialogue(), Dialogue()
        one, two = first._model(), second._model()
        assert one.temperature == two.temperature == model_settings.llm.temperature
        assert first._model() is one
        assert one.http_client is not two.http_client
        assert one.http_async_client is not two.http_async_client
        assert not one.http_client.is_closed and not one.http_async_client.is_closed
        await first.close()
        assert one.http_client.is_closed and one.http_async_client.is_closed
        assert not two.http_client.is_closed and not two.http_async_client.is_closed
        three = third._model()
        assert three.http_client is not one.http_client
        assert three.http_async_client is not one.http_async_client
        assert not three.http_client.is_closed and not three.http_async_client.is_closed
        await first.close()  # Repeated close is harmless.
        await second.close()
        await third.close()
        assert two.http_client.is_closed and two.http_async_client.is_closed
        assert three.http_client.is_closed and three.http_async_client.is_closed
    asyncio.run(run())


def test_new_event_loop_receives_open_independent_clients(model_settings):
    previous = []

    async def run():
        dialogue = Dialogue()
        model = dialogue._model()
        assert not model.http_async_client.is_closed
        assert all(model.http_async_client is not client for client in previous)
        previous.append(model.http_async_client)
        await dialogue.close()
        assert model.http_async_client.is_closed

    asyncio.run(run())
    asyncio.run(run())


def test_injected_model_and_its_clients_remain_caller_owned():
    calls = []
    class ExternalClient:
        def close(self):
            calls.append("close")
    model = SimpleNamespace(root_client=ExternalClient(), root_async_client=ExternalClient())
    dialogue = Dialogue(model=model)
    asyncio.run(dialogue.close())
    assert dialogue.model is model
    assert not calls


@pytest.mark.parametrize("running_loop", [False, True])
def test_failed_model_initialization_closes_both_constructed_clients(model_settings, monkeypatch, running_loop):
    import langchain_openai
    clients = []
    def failure(**kwargs):
        clients.extend((kwargs["http_client"], kwargs["http_async_client"]))
        raise ValueError("simulated model initialization failure")
    monkeypatch.setattr(langchain_openai, "ChatOpenAI", failure)
    dialogue = Dialogue()

    def construct():
        with pytest.raises(ValueError, match="simulated model initialization failure"):
            dialogue._model()
        assert dialogue.model is None
        assert clients[0].is_closed

    async def run():
        construct()
        await dialogue.close()

    if running_loop:
        asyncio.run(run())
    else:
        construct()
    assert clients[1].is_closed
    assert dialogue._http_clients is None


def test_failed_async_client_construction_closes_already_created_sync_client(model_settings, monkeypatch):
    import openai
    original, clients = openai.DefaultHttpxClient, []
    def sync(**kwargs):
        client = original(**kwargs)
        clients.append(client)
        return client
    def asynchronous(**kwargs):
        raise ValueError("simulated async client initialization failure")
    monkeypatch.setattr(openai, "DefaultHttpxClient", sync)
    monkeypatch.setattr(openai, "DefaultAsyncHttpxClient", asynchronous)
    with pytest.raises(ValueError, match="simulated async client initialization failure"):
        Dialogue()._model()
    assert len(clients) == 1 and clients[0].is_closed


def test_sync_cleanup_still_runs_if_async_close_fails():
    calls = []
    class SyncClient:
        def close(self):
            calls.append("sync")
    class AsyncClient:
        async def aclose(self):
            calls.append("async")
            raise RuntimeError("simulated close failure")
    dialogue = Dialogue()
    dialogue._http_clients = (SyncClient(), AsyncClient())
    with pytest.raises(RuntimeError, match="simulated close failure"):
        asyncio.run(dialogue.close())
    assert calls == ["async", "sync"]
    assert dialogue._http_clients is None
