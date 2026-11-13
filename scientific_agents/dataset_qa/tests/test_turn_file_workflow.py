"""Changed requests, scoped discovery and terminal file delivery across turns."""
import asyncio
from copy import deepcopy
import csv
import io
import json

import pytest

from mcp_servers.corpus_mcp import mcp
from ..capabilities import TASK
from ..contracts import QAError, Server
from ..execution import Execution
from ..mcp import MCPGateway, Tool, ToolSession
from ..operations import Operations
from ..plan_runtime import install_plan
from ..planning import Plan, outcome_status, require_delivery
from ..routing import select_tools
from ..responses import recovery_search_summary
from ..service import DatasetQA
from .test_dataset_qa import action, collect, engine, result_cards, session
from .test_decisions import BareDialogue, payload, text
from .test_file_pipeline import files, query_args
from .test_local_artifacts import download_client, file_plan
from .test_planning import approve


REQUEST = ("我想从 PubChem 找一批和这个分子相似的化合物，用来做后续筛选，"
    "SMILES 是 CC(=O)OC1=CC=CC=C1C(=O)O。相似度至少 {threshold}%，"
    "分子量在 100 到 500 之间，LogP 在 -1 到 5 之间，先帮我下载 {limit} 条，保存成 CSV。")

SOURCE_AND_FILE_TOOLS = {"query_pubchem_compounds", "export_dataset", "get_corpus_file_schema", "read_corpus_file_records"}


def test_source_scope_cold_warm_and_empty_load_query():
    async def run():
        gateway = MCPGateway({"piflow-corpus": Server(mcp)})
        for threshold, limit in [(80, 1000), (90, 100)]:
            async with gateway.session() as tools:
                await tools.prepare(REQUEST.format(threshold=threshold, limit=limit),
                    [{"server": "piflow-corpus", "name": "get_corpus_dataset_detail"}])
                assert {tool.name for tool in tools.loaded.values()} == SOURCE_AND_FILE_TOOLS
                await tools.load("piflow-corpus")
                assert {tool.name for tool in tools.loaded.values()} == SOURCE_AND_FILE_TOOLS
                # A source hint does not erase the rest of the tool catalogue.
                page = await tools.load("piflow-corpus", offset=4)
                assert any(item["tool"] == "search_corpus_datasets" for item in page["items"])
                # Explicit discovery of another group is still supported.
                await tools.load("piflow-corpus", group="corpus")
                assert any(tool.name == "search_corpus_datasets" for tool in tools.loaded.values())
    asyncio.run(run())


def test_source_routing_is_metadata_driven_and_supports_multiple_sources():
    def tool(name, source):
        return Tool("server", name, "find and process", {"type": "object", "properties": {}}, {},
            {"piflow": {"qa": {"routing": {"group": name, "source": source}}}})
    tools = [tool("old", "ArchiveA"), tool("new", "ArchiveB"), tool("convert", "")]
    assert [t.name for t in select_tools(tools, "ArchiveB", recent=[("server", "old")])] == ["new", "convert", "old"]
    assert len(select_tools(tools, "ArchiveA ArchiveB")) == 3
    assert len(select_tools(tools, "unqualified request")) == 3


def test_same_session_changed_values_execute_new_query_and_deliver_csv(engine, files, download_client, monkeypatch):
    calls = []
    original = ToolSession.call
    async def capture(tools, alias, arguments, **kwargs):
        calls.append((tools.loaded[alias].name, deepcopy(arguments)))
        return await original(tools, alias, arguments, **kwargs)
    monkeypatch.setattr(ToolSession, "call", capture)

    async def run():
        service = DatasetQA(engine, BareDialogue(), MCPGateway({"piflow-corpus": Server(mcp)}))
        sid = session(service)
        sources = []
        try:
            for threshold, limit in [(80, 1000), (90, 100)]:
                plan = file_plan()
                plan["steps"][0]["arguments"] = query_args(similarity_threshold=threshold, limit=limit)
                def understand(messages, definitions):
                    names = {d["function"]["name"] for d in definitions}
                    assert not any(n.endswith("_query_pubchem_compounds") for n in names)
                    # A saved resource keeps direct consumers available; a
                    # changed query itself still requires a reviewed plan.
                    if threshold == 80:
                        assert not any(n.startswith("mcp_") for n in names)
                    else:
                        assert any(n.endswith("_export_dataset") for n in names)
                    remember = next(d["function"] for d in definitions if d["function"]["name"] == "remember")
                    assert "plan" in remember["parameters"]["properties"]
                    assert "query_pubchem_compounds" in remember["description"]
                    assert "export_dataset" in remember["description"] or any(n.endswith("_export_dataset") for n in names)
                    assert str(threshold) in next(m.content for m in messages if m.id == "qa-current-request")
                    return action("remember", plan=plan)
                service.dialogue = BareDialogue(understand, approve, text())
                events = await collect(service, sid, REQUEST.format(threshold=threshold, limit=limit), rid=str(threshold))
                saved = payload(service, sid, events)
                assert saved.get("error") is None
                assert saved["plan"]["acceptance"]["file"]["state"] == "accepted"
                assert len(service.dialogue.inputs) == 3  # plan, review, answer; no decisions between MCP steps
                cards = result_cards(events)
                assert len(cards) == 1
                output = cards[0]["data"]["items"][0]
                assert output["resource"]["format"] == "csv"
                response = download_client.get(output["downloadUrl"])
                assert response.status_code == 200
                assert [row["CID"] for row in csv.DictReader(io.StringIO(response.text))] == ["1", "2"]
                sources.append(output["resource"]["source_ref"])
                final_context = json.loads(service.dialogue.inputs[-1][0][1].content)
                assert "search_outcomes" not in final_context
                assert len(saved["operations"]) == 2
            assert sources[0] != sources[1]
            assert [name for name, _ in calls] == ["query_pubchem_compounds", "export_dataset"]*2
            assert calls[0][1] == query_args()
            assert calls[2][1] == query_args(similarity_threshold=90, limit=100)
            assert calls[1][1]["source_ref"] != calls[3][1]["source_ref"]
            assert len(files.requests) == 4
        finally:
            await service.close()
    asyncio.run(run())


@pytest.mark.parametrize("mistake", ["wrong_source", "intermediate_is_final"])
def test_bad_first_action_is_corrected_before_any_upstream_call(engine, files, mistake):
    async def run():
        gateway = MCPGateway({"piflow-corpus": Server(mcp)})
        async with gateway.session() as tools:
            catalogue = await tools.tools("piflow-corpus")
        name = "search_corpus_datasets" if mistake == "wrong_source" else "query_pubchem_compounds"
        alias = next(t.alias for t in catalogue if t.name == name)
        args = {"query": "PubChem"} if mistake == "wrong_source" else query_args()
        def repair(messages, definitions):
            assert not files.requests
            return action("remember", plan=file_plan())
        dialogue = BareDialogue(action(alias, **args, **{TASK: {"complete_request": True}}), repair, approve, text())
        service = DatasetQA(engine, dialogue, gateway)
        try:
            sid = session(service)
            events = await collect(service, sid, REQUEST.format(threshold=80, limit=1000))
            saved = payload(service, sid, events)
            assert saved.get("error") is None
            assert len(saved["operations"]) == 2
            assert len(files.requests) == 2
            assert result_cards(events)[0]["data"]["items"][0]["resource"]["format"] == "csv"
        finally:
            await service.close()
    asyncio.run(run())


def test_terminal_format_is_checked_even_if_model_omits_the_check(engine, files):
    async def run():
        service = DatasetQA(engine, BareDialogue(), MCPGateway({"piflow-corpus": Server(mcp)}))
        try:
            async with service.gateway.session() as tools:
                await tools.load("piflow-corpus", query="PubChem CSV")
                state, execution = {}, Execution()
                await install_plan(service, "alice", session(service), Plan.model_validate(file_plan()), tools, execution, state, {})
                saved = state["plan"]
                saved["reviewed"] = saved["revision"]
                operation = execution.operations.get(saved["operations"]["export"])
                operation.update(state="succeeded", attempts=[{"state": "succeeded", "result_id": "export:0"}])
                cards = [{"result_id": "export:0", "data": {"record_count": 100,
                    "resource": {"source_ref": "reference", "format": "jsonl"}}}]
                assert outcome_status(saved, execution.operations, cards)["file"]["state"] == "incomplete"
                with pytest.raises(QAError, match="成果尚未全部核实"):
                    require_delivery(saved, execution.operations, cards)
                cards[0]["data"]["resource"]["format"] = "csv"
                require_delivery(saved, execution.operations, cards)
                inconsistent = file_plan()
                inconsistent["outcomes"][0]["checks"] = [{"path": "/resource/format", "test": "equals", "value": "csv"}]
                inconsistent["steps"][-1]["arguments"]["format"] = "jsonl"
                with pytest.raises(QAError, match="终端步骤参数"):
                    await install_plan(service, "alice", session(service), Plan.model_validate(inconsistent), tools, Execution(), {}, {})
        finally:
            await service.close()
    asyncio.run(run())


def test_unrelated_empty_search_does_not_override_requested_file_feedback():
    operations = Operations([
        {"id": "aux", "required": False, "inferred": True, "attempts": [],
            "search": {"done": True, "stop": "exhausted", "records": []}},
        {"id": "file", "required": True, "attempts": []},
    ])
    assert recovery_search_summary(operations, []) == ""
    # A genuinely requested empty catalogue search keeps its original message.
    operations.items[0]["required"] = True
    assert "暂未找到匹配的数据集" in recovery_search_summary(operations, [])
