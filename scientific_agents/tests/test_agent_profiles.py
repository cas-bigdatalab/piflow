"""Agent profiles isolate capabilities and state without changing the QA defaults."""
import asyncio
from dataclasses import replace
from hashlib import sha256
import json

import pytest
from sqlalchemy import inspect, update

from .. import loading
from ..agent_profiles import AgentProfile, DATASET_QA_PROFILE, ToolScope
from ..dataset_qa.contracts import QAError
from ..dataset_qa.dialogue import Dialogue, SYSTEM, builtin_definitions
from ..dataset_qa.persistence import Store, dumps
from ..dataset_qa.prompts import system_prompt
from ..dataset_qa.responses import notice
from ..dataset_qa.service import DatasetQA
from ..dataset_qa.tests.test_dataset_qa import Backend, action, collect, definition, engine, remote, session
from ..dataset_qa.tests.test_decisions import BareDialogue, text
from ..pubchem.profile import PROFILE


def test_default_profile_uses_shared_prompt_and_preserves_storage_contract():
    dialogue = Dialogue(model=object())
    assert dialogue.agent_profile == DATASET_QA_PROFILE
    assert SYSTEM and system_prompt() == system_prompt(DATASET_QA_PROFILE) == SYSTEM
    assert dialogue.messages("你好", {})[0].content == SYSTEM
    assert DATASET_QA_PROFILE.storage_namespace == "dataset_qa"
    assert DATASET_QA_PROFILE.session_prefix == "qa"
    assert DATASET_QA_PROFILE.max_concurrency == 8
    names = {value["function"]["name"] for value in builtin_definitions()}
    scoped = {value["function"]["name"] for value in builtin_definitions(agent_profile=PROFILE)}
    assert names - scoped == {"resolve_resource"}
    prompt = system_prompt(PROFILE)
    assert "PubChem" in prompt and "remember.plan" in prompt
    assert "six actually returned" not in prompt and "resolve_resource" not in prompt
    assert len(prompt) < len(SYSTEM)
    error = QAError("tool_failed", "internal details")
    assert "其他化合物" in notice(error, resource_noun=PROFILE.resource_noun)
    assert "其他数据集" in notice(error)
    assert "internal details" not in notice(error)


@pytest.mark.parametrize("change", [
    {"agent_id": "../escape"}, {"namespace": "qa;delete"}, {"id_prefix": "bad-id"},
    {"features": {"directory_lookup"}}, {"features": frozenset({"unknown"})},
    {"tool_scope": [ToolScope("data", tools=("search",))]},
    {"max_concurrency": True}, {"max_concurrency": 0}, {"instructions": []}, {"label": 1},
])
def test_invalid_or_mutable_profile_is_rejected(change):
    with pytest.raises(ValueError):
        AgentProfile(**{"agent_id": "example", "label": "示例", **change})


@pytest.mark.parametrize("change", [{"server": None}, {"groups": ["example"]}, {"tools": (1,)}])
def test_invalid_tool_scope_is_rejected(change):
    with pytest.raises(ValueError):
        ToolScope(**{"server": "data", "tools": ("search",), **change})


def test_registry_rejects_cross_agent_storage_collisions(monkeypatch):
    collision = replace(PROFILE, namespace="dataset_qa")
    monkeypatch.setitem(loading.AGENTS, "pubchem", loading.AgentSpec.tool_agent(collision))
    with pytest.raises(ValueError, match="命名空间"):
        loading.validate_enabled(["dataset_qa", "pubchem"])


def test_storage_namespaces_preserve_qa_ids_and_isolate_memory_tasks(engine):
    qa, specialist = Store(engine), Store(engine, agent_profile=PROFILE)
    qs = qa.create("alice", "QA", "same")
    ps = specialist.create("alice", "PubChem", "same")
    assert qs["id"] == "qa-" + sha256(dumps(["alice", "same"]).encode()).hexdigest()[:32]
    assert ps["id"].startswith("pubchem-") and ps["id"] != qs["id"]
    for own, other, row in [(qa, specialist, qs), (specialist, qa, ps)]:
        tid = own.submit("alice", row["id"], "turn", {"message": "first"}, None, "owner")[0]["id"]
        own.write("alice", row["id"], tid, context={"memory": {"choice": row["title"]}})
        with pytest.raises(QAError, match="会话不存在"):
            other.session("alice", row["id"])
        assert other.task_session("alice", tid) is None
        assert own.task_session("bob", tid) is None
        own.finish("alice", row["id"], tid, "COMPLETED", message="已保存")
    assert json.loads(qa.session("alice", qs["id"])["context"])["memory"] == {"choice": "QA"}
    restored = Store(engine, agent_profile=PROFILE)
    assert json.loads(restored.session("alice", ps["id"])["context"])["memory"] == {"choice": "PubChem"}
    qa.delete("alice", qs["id"])
    assert restored.session("alice", ps["id"])["status"] == "ACTIVE"
    assert set(inspect(engine).get_table_names()) == {
        prefix + "_" + suffix for prefix in ("dataset_qa", "agent_pubchem")
        for suffix in ("sessions", "tasks", "items", "events")}


def test_expired_task_recovery_only_touches_its_agent_namespace(engine):
    qa, specialist = Store(engine), Store(engine, agent_profile=PROFILE)
    qs, ps = qa.create("alice", "QA", "same"), specialist.create("alice", "PubChem", "same")
    qt = qa.submit("alice", qs["id"], "turn", {"message": "first"}, None, "qa-owner")[0]
    pt = specialist.submit("alice", ps["id"], "turn", {"message": "first"}, None, "old-process")[0]
    with specialist.transaction() as conn:
        conn.execute(update(specialist.tasks).where(specialist.tasks.c.id == pt["id"]).values(expires=0))
    assert qa.heartbeat("qa-owner") == {qt["id"]}
    assert specialist.task("alice", ps["id"], pt["id"])["status"] == "RUNNING"
    restored = Store(engine, agent_profile=PROFILE)
    assert restored.heartbeat("new-process") == set()
    assert restored.task("alice", ps["id"], pt["id"])["status"] == "FAILED"
    assert restored.session("alice", ps["id"])["active_task_id"] is None
    assert qa.task("alice", qs["id"], qt["id"])["status"] == "RUNNING"
    assert qa.session("alice", qs["id"])["active_task_id"] == qt["id"]


def test_profile_filters_discovery_cache_and_execution_before_transport():
    backend = Backend()
    for item in backend.catalog["data"]:
        item.meta = {"piflow": {"qa": {"routing": {"group": "catalogue" if item.name == "search" else "inspection"}}}}
    profile = AgentProfile("inspector", "内容助手", tool_scope=(ToolScope("data", groups=("inspection",)),))
    parent = backend.gateway()
    scoped = parent.for_profile(profile)

    async def run():
        async with parent.session() as original:
            full = await original.tools("data")
            assert len(full) == 4
        assert not scoped.cache
        async with scoped.session() as tools:
            assert [row["name"] for row in tools.list_servers()["items"]] == ["data"]
            for name in ("compute", "unconfigured"):
                with pytest.raises(QAError, match="未配置"):
                    await tools.load(name)
            allowed = await tools.tools("data")
            assert {item.name for item in allowed} == {"inspect", "preview", "sample"}
            assert (await tools.load("data", group="catalogue"))["items"] == []
            hidden = next(item for item in full if item.name == "search")
            assert tools.include([hidden])["items"] == []
            # A stale or externally inserted plan entry is still checked at dispatch.
            tools.loaded[hidden.alias] = hidden
            assert all(row["function"]["name"] != hidden.alias for row in tools.definitions())
            for call in (tools.call, tools.call_isolated):
                with pytest.raises(QAError):
                    await call(hidden.alias, {"query": "bypass"})
            visible = next(item for item in allowed if item.name == "inspect")
            tools.include([visible])
            await tools.call(visible.alias, {"reference": "a"})
        async with scoped.session() as tools:
            assert {item.name for item in await tools.tools("data")} == {"inspect", "preview", "sample"}
        assert backend.lists == ["data", "data"]
        assert backend.calls == [("data", "inspect", {"reference": "a"})]
        assert "compute" not in backend.connections
        assert len(parent.cache["data"][2]) == 4 and len(scoped.cache["data"][2]) == 3
    asyncio.run(run())


def test_disallowed_invalid_definitions_do_not_poison_scoped_discovery():
    backend = Backend()
    backend.catalog["data"] += [definition("broken"), definition("broken")]
    backend.catalog["data"][0].inputSchema = {"type": "not-json-schema"}
    profile = AgentProfile("inspector", "内容助手", tool_scope=(ToolScope("data", tools=("inspect",)),))

    async def run():
        async with backend.gateway(agent_profile=profile).session() as tools:
            assert [item.name for item in await tools.tools("data")] == ["inspect"]
            assert tools.definition_errors["data"] == []
    asyncio.run(run())


def test_no_scope_is_deny_by_default():
    backend = Backend()
    profile = AgentProfile("empty", "未配置能力")

    async def run():
        async with backend.gateway(agent_profile=profile).session() as tools:
            assert tools.list_servers()["items"] == []
            await tools.prepare("anything")
            assert tools.definitions() == []
        assert not backend.connections
    asyncio.run(run())


def test_third_domain_uses_same_runtime_without_qa_or_pubchem_branches(engine):
    from ..dataset_qa.capabilities import TASK

    profile = AgentProfile("calculator", "计算助手", instructions="Compute using the provided tools.",
        tool_scope=(ToolScope("compute", tools=("multiply",)),))
    backend = Backend()
    dialogue = BareDialogue(remote("multiply", x=6, y=7, **{TASK: {"complete_request": True}}), text("结果为 42。"))
    original = backend.gateway()
    service = DatasetQA(engine, dialogue, original, agent_profile=profile)

    async def run():
        try:
            sid = session(service)
            values = await collect(service, sid, "计算 6 乘 7")
            assert values[-1]["status"] == "COMPLETED"
            assert backend.calls == [("compute", "multiply", {"x": 6, "y": 7})]
            assert len(dialogue.inputs) == 2  # One operation decision, one final answer.
            assert all("计算助手" in messages[0].content for messages, _ in dialogue.inputs)
            assert service.gateway is not original and original.agent_profile == DATASET_QA_PROFILE
            assert service.session_view(service.store.session("alice", sid))["agent_id"] == "calculator"
            assert service.resources.store is None and not service.resources.workers
            assert not any("resource_" in name for name in inspect(engine).get_table_names())
            with pytest.raises(QAError, match="未开放"):
                await service._builtin("alice", sid, "unused", "resolve_resource", {}, None, {})
        finally:
            await service.close()
    asyncio.run(run())
    adapter = loading.AgentSpec.tool_agent(profile).adapter_class()
    assert adapter.agent_id == "calculator" and adapter.label == "计算助手"
