"""Specialist entry through the real runtime, MCP server and download route.

Only upstream PubChem HTTP and model decisions are deterministic test doubles.
"""
import asyncio
import csv
import io
import json

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import inspect

from mcp_servers.corpus_mcp import mcp
from ..dataset_qa.capabilities import OBJECT, TASK
from ..dataset_qa.contracts import QAError, Server
from ..dataset_qa.mcp import MCPGateway, ToolSession
from ..dataset_qa.service import DatasetQA
from ..dataset_qa.tests.test_dataset_qa import action, collect, engine, result_cards, session
from ..dataset_qa.tests.test_decisions import BareDialogue, payload, text
from ..dataset_qa.tests.test_file_pipeline import files, query_args
from ..dataset_qa.tests.test_local_artifacts import download_client
from ..dataset_qa.tests.test_planning import approve
from ..dataset_qa.tests.test_turn_file_workflow import REQUEST
from ..dataset_qa.tests.test_workflow_input import compact_plan
from ..integration import install_scientific_agents
from ..pubchem.profile import PROFILE
from ..unified.schemas import PREFIX
from .test_loading import identity, resources


def test_scoped_real_mcp_keeps_qa_catalogue_and_blocks_group_escape():
    parent = MCPGateway({"piflow-corpus": Server(mcp)})
    scoped = parent.for_profile(PROFILE)

    async def run():
        async with parent.session() as tools:
            original = await tools.tools("piflow-corpus")
            assert len(original) == 8
        for warm in (False, True):
            async with scoped.session() as tools:
                await tools.prepare(REQUEST.format(threshold=80, limit=1000))
                assert {tool.name for tool in tools.loaded.values()} == {"query_pubchem_compounds", "export_dataset"}
                assert (await tools.load("piflow-corpus", group="corpus", limit=20))["items"] == []
                assert not (await tools.load("piflow-corpus", offset=2))["items"]
                groups = tools.list_servers()["items"][0]["groups"]
                assert {item["group"] for item in groups} == {"pubchem", "data_processing"}
                for tool in original:
                    if tool.name not in {"query_pubchem_compounds", "export_dataset"}:
                        assert tools.include([tool])["items"] == []
        async with parent.session() as tools:
            assert {item.name for item in await tools.tools("piflow-corpus")} == {item.name for item in original}
    asyncio.run(run())


def test_pubchem_plan_changed_conditions_csv_links_and_model_budget(engine, files, download_client, monkeypatch):
    calls = []
    original = ToolSession.call

    async def record(tools, alias, arguments, **kwargs):
        calls.append((tools.loaded[alias].name, dict(arguments)))
        return await original(tools, alias, arguments, **kwargs)

    monkeypatch.setattr(ToolSession, "call", record)
    service = DatasetQA(engine, gateway=MCPGateway({"piflow-corpus": Server(mcp)}), agent_profile=PROFILE)

    async def run():
        sid = session(service)
        try:
            for index, (threshold, limit) in enumerate(((80, 1000), (90, 100))):
                dialogue = BareDialogue(action("remember", plan=compact_plan(threshold, limit)), approve,
                    text("已取得两条符合条件的记录，未达到请求数量。CSV 文件见下载链接。"))
                service.dialogue = dialogue
                values = await collect(service, sid, REQUEST.format(threshold=threshold, limit=limit), str(index))
                saved = payload(service, sid, values)
                assert saved["plan"]["acceptance"]["export"]["state"] == "accepted"
                assert [item["state"] for item in saved["operations"]] == ["succeeded", "succeeded"]
                assert calls[index * 2][0] == "query_pubchem_compounds"
                assert calls[index * 2][1] == query_args(similarity_threshold=threshold, limit=limit)
                assert calls[index * 2 + 1][0] == "export_dataset"
                assert calls[index * 2 + 1][1]["format"] == "csv"
                assert len(dialogue.inputs) == 3  # Plan, review, final; no extra per-step model call.
                assert all("Current assistant: PubChem" in messages[0].content for messages, _ in dialogue.inputs)
                assert all("six actually returned" not in messages[0].content for messages, _ in dialogue.inputs)
                cards = result_cards(values)
                assert len(cards) == 1 and set(cards[0]) == {"result_id", "view_type", "title", "data"}
                result = cards[0]["data"]["items"][0]
                assert result["resource"]["format"] == "csv" and result["record_count"] == 2
                response = download_client.get(result["downloadUrl"])
                assert response.status_code == 200 and "attachment" in response.headers["content-disposition"]
                assert [row["CID"] for row in csv.DictReader(io.StringIO(response.text))] == ["1", "2"]
                assert download_client.get(result["downloadUrl"], headers={"Range": "bytes=0-31"}).status_code == 206
                history = await service.get_session("alice", sid)
                answer = [item["payload"]["text"] for item in history["items"] if item["item_type"] == "ASSISTANT_MESSAGE"][-1]
                assert result["downloadUrl"] in answer
            assert len(calls) == 4 and len(files.requests) == 4
            assert service.resources.store is None and not service.resources.workers
            assert not any(name.startswith("dataset_qa_") for name in inspect(engine).get_table_names())
        finally:
            await service.close()
    asyncio.run(run())


def test_followup_export_after_restart_uses_owned_resource_without_requery(engine, files, download_client):
    async def run():
        first = DatasetQA(engine, gateway=MCPGateway({"piflow-corpus": Server(mcp)}), agent_profile=PROFILE)
        sid = session(first)
        try:
            plan = {"steps": compact_plan()["steps"][:1]}
            first.dialogue = BareDialogue(action("remember", plan=plan), approve, text("已取得两条记录。"))
            values = await collect(first, sid, "PubChem 按条件查找化合物，不需要转换文件")
            assert result_cards(values)[0]["data"]["items"][0]["resource"]["format"] == "jsonl"
            handle = first.artifacts.recent("alice")[0]["handle"]
        finally:
            await first.close()

        restored = DatasetQA(engine, gateway=MCPGateway({"piflow-corpus": Server(mcp)}), agent_profile=PROFILE)
        qa = DatasetQA(engine, gateway=MCPGateway({"piflow-corpus": Server(mcp)}))
        try:
            assert qa.artifacts.recent("alice") == []
            with pytest.raises(QAError):
                qa.artifacts.get("alice", handle)
            with pytest.raises(QAError):
                restored.artifacts.get("bob", handle)

            def export(messages, definitions):
                context = json.loads(messages[1].content)
                assert handle in json.dumps(context)
                alias = next(item["function"]["name"] for item in definitions
                    if item["function"]["name"].endswith("_export_dataset"))
                return action(alias, format="csv", **{OBJECT: handle,
                    TASK: {"complete_request": True, "operation": "export", "output_format": "csv"}})

            restored.dialogue = BareDialogue(export, text("已将这些记录保存为 CSV。"))
            values = await collect(restored, sid, "把这些记录保存成 CSV", "export")
            result = result_cards(values)[0]["data"]["items"][0]
            assert result["resource"]["format"] == "csv" and result["record_count"] == 2
            assert download_client.get(result["downloadUrl"]).status_code == 200
            assert len(files.requests) == 2  # No new PubChem query for a format change.
            assert len(restored.dialogue.inputs) == 2
            assert not any(item["state"] != "succeeded" for item in payload(restored, sid, values)["operations"])
            other = session(restored, request="another-session")
            assert restored.artifacts.get("alice", handle)["resource"]["record_count"] == 2
            assert (await restored.get_session("alice", other))["items"] == []
            qa_session = session(qa)
            assert (await qa.get_session("alice", qa_session))["items"] == []
        finally:
            await restored.close()
            await qa.close()
    asyncio.run(run())


@pytest.mark.parametrize("qa_enabled", [False, True])
def test_unified_routes_startup_selection_history_and_disabled_ownership(tmp_path, monkeypatch, identity, files, qa_enabled):
    config = tmp_path / "mcp.yaml"
    config.write_text("{}", encoding="utf-8")
    monkeypatch.setenv("DATASET_QA_MCP_CONFIG", str(config))
    monkeypatch.delenv("DATASET_QA_MCP_URL", raising=False)
    host = resources(tmp_path)
    enabled = ["pubchem", *(["dataset_qa"] if qa_enabled else [])]

    def app_for(names):
        app = FastAPI()
        install_scientific_agents(app, resources=host, enabled_agents=names)
        return app

    app = app_for(enabled)
    headers = {"Authorization": "Bearer alice"}
    with TestClient(app, headers=headers) as client:
        agents = client.get(PREFIX).json()["result"]["items"]
        assert {item["agent_id"] for item in agents} == set(enabled)
        created = client.post(PREFIX + "/sessions", json={"agent_id": "pubchem", "request_id": "same"})
        assert created.status_code == 200
        row = created.json()["result"]
        sid = row["session_id"]
        assert row["agent_id"] == "pubchem"
        service = app.state.scientific_agents.agent_states["pubchem"]
        service.dialogue = BareDialogue(action("remember", plan=compact_plan()), approve, text("已生成 CSV 文件。"))
        response = client.post(PREFIX + f"/sessions/{sid}/tasks/plan/pre-bind/stream",
            json={"user_request": REQUEST.format(threshold=80, limit=1000), "request_id": "first"})
        assert response.status_code == 200
        events = [json.loads(line[6:]) for line in response.text.splitlines() if line.startswith("data: ")]
        assert events[-1]["type"] == "done" and events[-1]["status"] == "COMPLETED"
        history = client.get(PREFIX + f"/sessions/{sid}").json()["result"]
        cards = [item for item in history["items"] if item["item_type"] == "RESULT_CARD"]
        assert len(cards) == 1
        tid = cards[0]["task_id"]
        assert tid.startswith("pubchem-task-")
        result = client.get(PREFIX + f"/tasks/{tid}/results").json()["result"]
        assert result["items"][0] == cards[0]["payload"]
        listed = client.get(PREFIX + "/sessions", params={"agent_id": "pubchem"}).json()["result"]
        assert [item["session_id"] for item in listed["items"]] == [sid]
        assert client.get(PREFIX + f"/sessions/{sid}", headers={"Authorization": "Bearer bob"}).status_code == 404
        assert not service.resources.workers
        if qa_enabled:
            other = client.post(PREFIX + "/sessions", json={"agent_id": "dataset_qa", "request_id": "same"}).json()["result"]
            assert other["session_id"] != sid and other["agent_id"] == "dataset_qa"
            assert client.get(PREFIX + f"/sessions/{other['session_id']}").json()["result"]["items"] == []
            assert app.state.scientific_agents.agent_states["dataset_qa"].artifacts.recent("alice") == []
        else:
            assert client.post(PREFIX + "/sessions", json={"agent_id": "dataset_qa"}).status_code == 409
    # Disabled history stays owned by PubChem, even without loading its runtime.
    with TestClient(app_for([]), headers=headers) as client:
        assert client.get(PREFIX + f"/sessions/{sid}").status_code == 409
        assert client.get(PREFIX + f"/sessions/{sid}/tasks/{tid}/results").status_code == 409
        assert client.get(PREFIX + f"/tasks/{tid}/results").status_code == 404
    with TestClient(app_for(["pubchem"]), headers=headers) as client:
        restored = client.get(PREFIX + f"/sessions/{sid}").json()["result"]
        assert restored["items"] == history["items"]
        assert client.delete(PREFIX + f"/sessions/{sid}").status_code == 200
        assert client.get(PREFIX + f"/sessions/{sid}").status_code == 404
