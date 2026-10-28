"""Startup selection, resource ownership and compatibility; no remote services."""
import asyncio
from contextlib import asynccontextmanager
from dataclasses import replace
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

from fastapi import FastAPI, HTTPException
import httpx
import pytest
from sqlalchemy import Column, MetaData, String, Table, delete, event, inspect, insert, select, text

from .. import loading
from ..integration import HostResources, install_scientific_agents
from ..shared import BindingStore


PREFIX = "/api/piflow/v1/agents"


def resources(tmp_path):
    return HostResources(tmp_path, f"sqlite:///{(tmp_path / 'shared.sqlite').as_posix()}")


class StubQA:
    def __init__(self, events, *, fail=False):
        self.events, self.fail = events, fail
        self.store = SimpleNamespace(session=lambda user, sid: None)

    async def start(self):
        self.events.append("qa.start")
        if self.fail:
            raise RuntimeError("QA startup interrupted")

    async def close(self):
        self.events.append("qa.close")


def forecast_stub(monkeypatch, events, *, fail=False):
    def create_app(**kwargs):
        @asynccontextmanager
        async def lifespan(app):
            events.append("forecast.start")
            try:
                if fail:
                    raise RuntimeError("Forecast startup interrupted")
                app.state.store = kwargs["shared_store"]()
                app.state.sessions = SimpleNamespace(lookup=lambda user, sid: None)
                app.state.delete_host_session = None
                yield
            finally:
                events.append("forecast.close")

        app = FastAPI(lifespan=lifespan)

        @app.post("/api/piflow/v1/forecast/sessions")
        def create_session():
            return {"session_id": "forecast-example"}

        return app

    monkeypatch.setitem(sys.modules, "scientific_agents.forecast.api",
        SimpleNamespace(PREFIX="/api/piflow/v1", create_app=create_app))


@pytest.fixture
def identity(monkeypatch):
    def current_user(*, token):
        return {"user_id": token}

    monkeypatch.setitem(sys.modules, "security.auth_dependency",
        SimpleNamespace(get_current_user=current_user))


@pytest.mark.parametrize("enabled", [[], ["forecast"], ["dataset_qa"], ["forecast", "dataset_qa"],
    ["dataset_qa", "forecast"]])
def test_selection_controls_routes_lifecycle_and_keeps_cross_dag(tmp_path, monkeypatch, identity, enabled):
    events = []
    forecast_stub(monkeypatch, events)

    @asynccontextmanager
    async def host_lifespan(app):
        events.append("host.start")
        try:
            yield {"existing": True}
        finally:
            events.append("host.close")

    app = FastAPI(lifespan=host_lifespan)

    @app.post("/api/piflow/v1/xdc/sessions")
    def cross_dag():
        return {"unchanged": True}

    qa = StubQA(events)
    install_scientific_agents(app, resources=resources(tmp_path), dataset_qa=qa, enabled_agents=enabled)
    assert set(app.state.unified_adapters) == {"cross_dag", *enabled}
    paths = {route.path for route in app.routes}
    assert ("/api/piflow/v1/forecast/sessions" in paths) == ("forecast" in enabled)

    async def run():
        async with app.router.lifespan_context(app) as original:
            assert original == {"existing": True}
            state = app.state.scientific_agents
            event.listen(state.store.engine, "engine_disposed", lambda engine: events.append("store.close"))
            assert set(state.agent_states) == set(enabled)
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test",
                    headers={"Authorization": "Bearer alice"}) as client:
                result = (await client.get(PREFIX)).json()["result"]
                assert {item["agent_id"] for item in result["items"]} == {"cross_dag", *enabled}
                assert (await client.post("/api/piflow/v1/xdc/sessions")).json() == {"unchanged": True}
                for name in set(loading.AGENTS) - set(enabled):
                    response = await client.post(PREFIX + "/sessions", json={"agent_id": name})
                    assert response.status_code == 409 and "已停用" in response.json()["message"]

    asyncio.run(run())
    names = {"forecast": "forecast", "dataset_qa": "qa"}
    assert events == ["host.start", *[names[name] + ".start" for name in enabled],
        *[names[name] + ".close" for name in reversed(enabled)], "store.close", "host.close"]
    assert not hasattr(app.state, "scientific_agents")


@pytest.mark.parametrize("document", ["", "null", "[]", "enabled_agents: null", "enabled_agents: forecast",
    "enabled_agents: [true]", "enabled_agents: [unknown]", "enabled_agents: [cross_dag]",
    "enabled_agents: [forecast, forecast]", "enabled_agents: []\nother: true", "enabled_agents: ["])
def test_invalid_config_is_rejected_before_loading(tmp_path, monkeypatch, document):
    path = tmp_path / "agents.yaml"
    path.write_text(document, encoding="utf-8")

    def unexpected(*args, **kwargs):
        pytest.fail("An invalid configuration must not load any agent")

    monkeypatch.setattr(loading, "AGENTS", {"forecast": SimpleNamespace(prepare=unexpected)})
    app = FastAPI()
    with pytest.raises(ValueError):
        install_scientific_agents(app, config_path=path)
    assert not hasattr(app.state, "scientific_agents_installed")


def test_config_defaults_empty_selection_and_working_directory(tmp_path, monkeypatch):
    monkeypatch.setattr(loading, "AGENTS_ROOT", tmp_path)
    assert loading.load_enabled() == loading.DEFAULT_AGENTS
    with pytest.raises(ValueError, match="不存在"):
        loading.load_enabled(tmp_path / "missing.yaml")
    (tmp_path / "configs").mkdir()
    config = tmp_path / "configs" / "agents.yaml"
    config.write_text("enabled_agents: []", encoding="utf-8-sig")
    monkeypatch.chdir(tmp_path.parent)
    assert loading.load_enabled() == ()
    config.write_text("enabled_agents: [dataset_qa]", encoding="utf-8")
    assert loading.load_enabled() == ("dataset_qa",)


def test_config_is_read_once_and_duplicate_install_is_rejected(tmp_path):
    config = tmp_path / "agents.yaml"
    config.write_text("enabled_agents: []", encoding="utf-8")
    app = FastAPI()
    install_scientific_agents(app, config_path=config, resources=resources(tmp_path))
    config.write_text("enabled_agents: [dataset_qa]", encoding="utf-8")
    assert app.state.enabled_scientific_agents == ()
    with pytest.raises(ValueError, match="重复安装"):
        install_scientific_agents(app, enabled_agents=[])

    async def run():
        async with app.router.lifespan_context(app):
            assert not app.state.scientific_agents.agent_states

    asyncio.run(run())


@pytest.mark.parametrize("fail", ["forecast", "qa"])
def test_startup_failure_releases_started_agents_and_shared_store(tmp_path, monkeypatch, fail):
    events = []
    forecast_stub(monkeypatch, events, fail=fail == "forecast")
    from .. import integration
    original_store = BindingStore

    def store(*args, **kwargs):
        value = original_store(*args, **kwargs)
        event.listen(value.engine, "engine_disposed", lambda engine: events.append("store.close"))
        return value

    monkeypatch.setattr(integration, "BindingStore", store)

    @asynccontextmanager
    async def host_lifespan(app):
        events.append("host.start")
        try:
            yield
        finally:
            events.append("host.close")

    app = FastAPI(lifespan=host_lifespan)
    install_scientific_agents(app, resources=resources(tmp_path), dataset_qa=StubQA(events, fail=fail == "qa"),
        enabled_agents=["forecast", "dataset_qa"])

    async def run():
        with pytest.raises(RuntimeError, match="startup interrupted"):
            async with app.router.lifespan_context(app):
                pytest.fail("An incomplete startup must not become ready")

    asyncio.run(run())
    middle = ["qa.start", "qa.close"] if fail == "qa" else []
    assert events == ["host.start", "forecast.start", *middle, "forecast.close", "store.close", "host.close"]
    assert not hasattr(app.state, "scientific_agents")


def test_lifespan_receives_original_exception_before_shared_cleanup(tmp_path, monkeypatch):
    events = []

    def prepare(*args):
        @asynccontextmanager
        async def lifespan(state):
            event.listen(state.store.engine, "engine_disposed", lambda engine: events.append("store.close"))
            try:
                yield
            except RuntimeError as exc:
                events.append(str(exc))
                raise
            finally:
                # Shared state and storage remain available until the agent closes.
                state.store.binding("alice", "cleanup", "dataset_qa")
                assert app.state.scientific_agents is state
                events.append("agent.close")

        return lifespan

    monkeypatch.setitem(loading.AGENTS, "dataset_qa", replace(loading.AGENTS["dataset_qa"], prepare=prepare))
    app = FastAPI()
    install_scientific_agents(app, resources=resources(tmp_path), enabled_agents=["dataset_qa"])

    async def run():
        with pytest.raises(RuntimeError, match="host interrupted"):
            async with app.router.lifespan_context(app):
                raise RuntimeError("host interrupted")

    asyncio.run(run())
    assert events == ["host interrupted", "agent.close", "store.close"]
    assert not hasattr(app.state, "scientific_agents")


def test_shutdown_failure_still_closes_other_agents_and_storage(tmp_path, monkeypatch):
    events = []
    forecast_stub(monkeypatch, events)

    class QA(StubQA):
        async def close(self):
            await super().close()
            raise RuntimeError("QA close interrupted")

    app = FastAPI()
    install_scientific_agents(app, resources=resources(tmp_path), dataset_qa=QA(events),
        enabled_agents=["forecast", "dataset_qa"])

    async def run():
        with pytest.raises(RuntimeError, match="QA close interrupted"):
            async with app.router.lifespan_context(app):
                event.listen(app.state.scientific_agents.store.engine, "engine_disposed",
                    lambda engine: events.append("store.close"))

    asyncio.run(run())
    assert events == ["forecast.start", "qa.start", "qa.close", "forecast.close", "store.close"]
    assert not hasattr(app.state, "scientific_agents")


def test_binding_schema_and_keys_survive_forecast_shutdown(tmp_path):
    from ..forecast.persistence import Store

    url = resources(tmp_path).database_url
    old = Store(url)
    old.binding("alice", "unified:existing", "forecast")
    old.close()
    shared = BindingStore(url)
    disposed = []
    event.listen(shared.engine, "engine_disposed", lambda engine: disposed.append(True))
    forecast = Store(url, shared=shared)
    try:
        assert forecast.engine is shared.engine
        assert forecast._lock is shared._lock
        assert shared.binding("alice", "unified:existing") == "forecast"
        forecast.binding("alice", "unified:qa", "dataset_qa")
        forecast.close()
        assert not disposed
        key = sha256(json.dumps(["alice", "unified:qa", "binding"]).encode()).hexdigest()
        with shared.engine.connect() as conn:
            assert conn.execute(select(shared.bindings.c.agent).where(shared.bindings.c.session == key)).scalar() == "dataset_qa"
    finally:
        shared.close()
    assert disposed == [True]


def test_disabled_legacy_session_is_preserved_and_never_rerouted(tmp_path, identity):
    res = resources(tmp_path)
    store = BindingStore(res.database_url)
    table = Table("forecast_sessions", MetaData(), Column("thread_id", String), Column("user_id", String))
    table.create(store.engine)
    with store.engine.begin() as conn:
        conn.execute(insert(table).values(thread_id="old-prediction", user_id="alice"))
    store.close()
    app = FastAPI()
    install_scientific_agents(app, resources=res, enabled_agents=[])

    async def run():
        async with app.router.lifespan_context(app):
            state = app.state.scientific_agents
            assert state.owner("alice", "old-prediction") == "forecast"
            assert state.owner("bob", "old-prediction") is None
            request = SimpleNamespace(headers={"authorization": "Bearer alice"})
            with pytest.raises(HTTPException) as error:
                await state.delete_host_session("alice", "old-prediction", request)
            assert error.value.status_code == 409
            assert state.session_services["forecast"].lookup("alice", "old-prediction")
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test",
                    headers={"Authorization": "Bearer alice"}) as client:
                assert (await client.get(PREFIX + "/sessions/old-prediction")).status_code == 409
                assert (await client.delete(PREFIX + "/sessions/old-prediction")).status_code == 409
                assert (await client.get(PREFIX + "/sessions/old-prediction",
                    headers={"Authorization": "Bearer bob"})).status_code == 404
            assert inspect(state.store.engine).has_table("forecast_sessions")

    asyncio.run(run())


def test_real_qa_uses_shared_resources_and_host_callbacks(tmp_path, monkeypatch, identity):
    from ..dataset_qa import service as qa_module

    class Dialogue:
        def __init__(self, **kwargs):
            pass

        async def close(self):
            pass

    monkeypatch.setattr(qa_module, "Dialogue", Dialogue)
    app = FastAPI()
    install_scientific_agents(app, resources=resources(tmp_path), enabled_agents=["dataset_qa"])

    async def run():
        async with app.router.lifespan_context(app):
            state = app.state.scientific_agents
            qa = state.agent_states["dataset_qa"]
            assert qa.store.engine is state.store.engine
            assert not inspect(state.store.engine).has_table("forecast_tasks")
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test",
                    headers={"Authorization": "Bearer alice"}) as client:
                response = await client.post(PREFIX + "/sessions", json={"agent_id": "dataset_qa", "request_id": "create"})
                assert response.status_code == 200, response.text
                sid = response.json()["result"]["session_id"]
                detail = await client.get(PREFIX + "/sessions/" + sid)
                assert detail.status_code == 200, detail.text
                assert state.session_services["dataset_qa"].lookup("alice", sid)
                assert state.session_services["dataset_qa"].lookup("bob", sid) is None
                request = SimpleNamespace(headers={"authorization": "Bearer bob"})
                with pytest.raises(HTTPException) as error:
                    await state.delete_host_session("alice", sid, request)
                assert error.value.status_code == 403
                request.headers["authorization"] = "Bearer alice"
                await state.delete_host_session("alice", sid, request)
                assert (await client.get(PREFIX + "/sessions/" + sid)).status_code == 404
        assert qa.ticker.done()

    asyncio.run(run())


def test_qa_history_survives_disable_and_reenable(tmp_path, monkeypatch, identity):
    from ..dataset_qa import service as qa_module

    monkeypatch.setattr(qa_module, "Dialogue", lambda **kwargs: SimpleNamespace())
    res = resources(tmp_path)

    async def run():
        sid = None
        for enabled in (["dataset_qa"], [], ["dataset_qa"]):
            app = FastAPI()
            install_scientific_agents(app, resources=res, enabled_agents=enabled)
            async with app.router.lifespan_context(app):
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test",
                        headers={"Authorization": "Bearer alice"}) as client:
                    if enabled:
                        created = await client.post(PREFIX + "/sessions", json={"agent_id": "dataset_qa",
                            "request_id": "persistent", "title": "保留历史"})
                        assert created.status_code == 200, created.text
                        current = created.json()["result"]["session_id"]
                        assert sid is None or current == sid
                        sid = current
                        detail = (await client.get(PREFIX + "/sessions/" + sid)).json()["result"]
                        assert detail["session"]["title"] == "保留历史"
                    else:
                        assert (await client.get(PREFIX + "/sessions/" + sid)).status_code == 409
                        assert app.state.scientific_agents.session_services["dataset_qa"].lookup("alice", sid)

    asyncio.run(run())


def test_unbound_active_session_keeps_cross_dag_ambiguity_check(tmp_path, monkeypatch, identity):
    from ..dataset_qa import service as qa_module
    from ..unified.adapters.cross_dag import CrossDagAdapter

    monkeypatch.setattr(qa_module, "Dialogue", lambda **kwargs: SimpleNamespace())
    monkeypatch.setattr(CrossDagAdapter, "owns_session", lambda self, sid: True)
    app = FastAPI()
    app.add_api_route("/api/piflow/v1/xdc/sessions", lambda: None, methods=["POST"])
    install_scientific_agents(app, resources=resources(tmp_path), enabled_agents=["dataset_qa"])

    async def run():
        async with app.router.lifespan_context(app):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test",
                    headers={"Authorization": "Bearer alice"}) as client:
                created = await client.post(PREFIX + "/sessions", json={"agent_id": "dataset_qa"})
                sid = created.json()["result"]["session_id"]
                store = app.state.scientific_agents.store
                with store.engine.begin() as conn:
                    conn.execute(delete(store.bindings))
                response = await client.get(PREFIX + "/sessions/" + sid)
                assert response.status_code == 409 and "归属不唯一" in response.json()["message"]
                assert store.binding("alice", "unified:" + sid) is None

    asyncio.run(run())


def test_real_forecast_lifecycle_shares_storage_and_keeps_session_api(tmp_path, monkeypatch, identity):
    from langgraph.checkpoint.memory import MemorySaver
    from ..forecast import api
    from ..forecast.config import Settings
    from ..forecast.dialogue import ExplicitInterpreter

    monkeypatch.setattr(api, "open_checkpointer", lambda *args: MemorySaver())
    monkeypatch.setenv("FORECAST_WARMUP", "1")
    warmed, disposed = [], []
    model = SimpleNamespace(warmup=lambda: warmed.append(True))
    res = resources(tmp_path)
    store = BindingStore(res.database_url)
    with store.engine.begin() as conn:
        conn.execute(text("CREATE TABLE chat_threads (id INTEGER PRIMARY KEY, thread_id TEXT UNIQUE, "
            "user_id TEXT, title TEXT, deleted BOOLEAN DEFAULT FALSE, "
            "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"))
    store.close()
    app = FastAPI()
    install_scientific_agents(app, resources=res, enabled_agents=["forecast"],
        settings=Settings(model_dir=tmp_path, root=tmp_path, sources=[]),
        predictor=model, interpreter=ExplicitInterpreter(), providers={})

    async def run():
        async with app.router.lifespan_context(app):
            state = app.state.scientific_agents
            forecast = state.agent_states["forecast"]
            event.listen(state.store.engine, "engine_disposed", lambda engine: disposed.append(True))
            assert forecast.store.engine is state.store.engine
            assert forecast.store._lock is state.store._lock
            assert warmed == [True]
            assert not inspect(state.store.engine).has_table("dataset_qa_sessions")
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test",
                    headers={"Authorization": "Bearer alice"}) as client:
                assert (await client.get("/api/piflow/v1/forecast/health")).json()["status"] == "ready"
                created = await client.post(PREFIX + "/sessions", json={"agent_id": "forecast", "title": "预测会话"})
                assert created.status_code == 200, created.text
                sid = created.json()["result"]["session_id"]
                assert state.store.binding("alice", "unified:" + sid) == "forecast"
                listed = await client.get(PREFIX + "/sessions?agent_id=forecast")
                assert listed.status_code == 200, listed.text
                assert listed.json()["result"]["items"][0]["session_id"] == sid
        assert not forecast.forecast.runner.watcher.is_alive()

    asyncio.run(run())
    assert disposed == [True]


def test_forecast_standalone_storage_still_owns_its_engine(tmp_path, monkeypatch):
    from langgraph.checkpoint.memory import MemorySaver
    from ..forecast import api
    from ..forecast.config import Settings
    from ..forecast.dialogue import ExplicitInterpreter

    monkeypatch.setattr(api, "open_checkpointer", lambda *args: MemorySaver())
    monkeypatch.setenv("FORECAST_WARMUP", "0")
    monkeypatch.delenv("FORECAST_DATABASE_URL", raising=False)
    monkeypatch.delenv("FORECAST_POSTGRES_DSN", raising=False)
    app = api.create_app(settings=Settings(model_dir=tmp_path, root=tmp_path, sources=[]),
        predictor=SimpleNamespace(), interpreter=ExplicitInterpreter(), providers={})
    disposed = []

    async def run():
        async with app.router.lifespan_context(app):
            assert app.state.store._owns_engine
            event.listen(app.state.store.engine, "engine_disposed", lambda engine: disposed.append(True))

    asyncio.run(run())
    assert disposed == [True]


@pytest.mark.parametrize("enabled", [[], ["dataset_qa"], ["forecast"]])
def test_disabled_modules_are_not_imported_in_fresh_process(tmp_path, enabled):
    script = r'''
import asyncio, importlib.abc, json, sys
from contextlib import asynccontextmanager
from pathlib import Path
from types import SimpleNamespace
from fastapi import FastAPI
enabled = json.loads(sys.argv[1])
disabled = set(("forecast", "dataset_qa")) - set(enabled)
class BlockDisabled(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if any(fullname == "scientific_agents." + name or
               fullname.startswith("scientific_agents." + name + ".") or
               fullname == "scientific_agents.unified.adapters." + name for name in disabled):
            raise AssertionError("Disabled agent imported: " + fullname)
sys.meta_path.insert(0, BlockDisabled())
if "forecast" in enabled:
    def create_app(**kwargs):
        @asynccontextmanager
        async def lifespan(app):
            app.state.sessions = SimpleNamespace(lookup=lambda *args: None)
            app.state.delete_host_session = None
            yield
        return FastAPI(lifespan=lifespan)
    sys.modules["scientific_agents.forecast.api"] = SimpleNamespace(PREFIX="/api/piflow/v1", create_app=create_app)
class QA:
    async def start(self): pass
    async def close(self): pass
from scientific_agents.integration import HostResources, install_scientific_agents
app = FastAPI()
install_scientific_agents(app, enabled_agents=enabled, dataset_qa=QA(),
    resources=HostResources(Path(sys.argv[2]), "sqlite:///" + sys.argv[2] + "/fresh.sqlite"))
async def run():
    async with app.router.lifespan_context(app):
        assert set(app.state.scientific_agents.agent_states) == set(enabled)
asyncio.run(run())
assert not any(name in sys.modules for agent in disabled for name in
    ("scientific_agents." + agent, "scientific_agents.unified.adapters." + agent))
'''
    completed = subprocess.run([sys.executable, "-c", script, json.dumps(enabled), tmp_path.as_posix()],
        cwd=Path(__file__).resolve().parents[2], env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1",
            "FORECAST_CONFIG": str(tmp_path / "missing-forecast.yaml"),
            "FORECAST_MODEL_DIR": str(tmp_path / "missing-model")},
        capture_output=True, text=True, timeout=30)
    assert completed.returncode == 0, completed.stdout + completed.stderr
