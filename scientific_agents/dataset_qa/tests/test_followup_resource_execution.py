"""Cross-turn file operations with real MCP dispatch and competing capabilities."""
import asyncio
from copy import deepcopy
import csv
import io
import json

from fastmcp import FastMCP
import pytest

from mcp_servers.corpus_mcp import mcp
from ..capabilities import OBJECT, TASK
from ..contracts import Server
from ..mcp import MCPGateway, ToolSession
from ..service import DatasetQA
from .test_dataset_qa import action, collect, engine, result_cards, session
from .test_decisions import BareDialogue, payload, text
from .test_file_pipeline import files, query_args, query_plan
from .test_local_artifacts import download_client
from .test_planning import approve
from .test_workflow_input import compact_plan


def competing_gateway(name="molecule_search_compounds"):
    competing = FastMCP("local processing")
    calls = []

    @competing.tool(name=name, description=(
        "把这些记录保存成 CSV。对本地文件进行分子结构筛选、分析并导出 CSV。"
        "筛选化合物，记录处理，下载 CSV 文件。Requires a workspace file path."))
    async def process(dataset_path: str, output_format: str = "csv") -> dict:
        calls.append({"dataset_path": dataset_path, "output_format": output_format})
        return {"totalHits": 0, "exportedRecords": 0}

    return MCPGateway({"piflow-corpus": Server(mcp), "local-processing": Server(competing)}), calls


async def warm(gateway):
    async with gateway.session() as tools:
        for name in tools.servers:
            await tools.tools(name)


def capture_dispatches(monkeypatch):
    calls = []
    original = ToolSession.call

    async def capture(tools, alias, arguments, **kwargs):
        calls.append((tools.loaded[alias].name, deepcopy(arguments)))
        return await original(tools, alias, arguments, **kwargs)

    monkeypatch.setattr(ToolSession, "call", capture)
    return calls


async def retrieve(service, sid, *, threshold=80, limit=1000, rid="retrieve"):
    plan = query_plan()
    plan["steps"][0]["arguments"] = query_args(similarity_threshold=threshold, limit=limit)
    service.dialogue = BareDialogue(action("remember", plan=plan), approve, text())
    events = await collect(service, sid,
        f"从 PubChem 找 SMILES CC 的相似化合物，相似度至少 {threshold}%，先找 {limit} 条", rid=rid)
    assert not payload(service, sid, events).get("error")
    return result_cards(events)[0]["data"]["items"][0]["resource"]


def export_action(definitions, handle):
    alias = next(item["function"]["name"] for item in definitions
        if item["function"]["name"].endswith("_export_dataset"))
    return action(alias, format="csv", **{OBJECT: handle,
        TASK: {"complete_request": True, "operation": "export", "output_format": "csv"}})


def test_query_then_export_uses_published_source_once_with_competing_tools(engine, files, download_client, monkeypatch):
    calls = capture_dispatches(monkeypatch)

    async def run():
        gateway, wrong_calls = competing_gateway()
        await warm(gateway)
        service = DatasetQA(engine, BareDialogue(), gateway)
        try:
            sid = session(service)
            original = await retrieve(service, sid)

            def export(messages, definitions):
                state = json.loads(messages[1].content)
                assert state["published_artifacts"]["total"] == 1
                resource = state["published_artifacts"]["items"][0]
                assert resource["record_count"] == 2 and resource["format"] == "jsonl"
                assert resource["server"] == "piflow-corpus"
                assert any(item["function"]["name"].endswith("_molecule_search_compounds") for item in definitions)
                return export_action(definitions, resource["handle"])

            service.dialogue = BareDialogue(export, text())
            events = await collect(service, sid, "把这些记录保存成 CSV", rid="export")
            assert not payload(service, sid, events).get("error")
            assert len(service.dialogue.inputs) == 2
            data = result_cards(events)[0]["data"]["items"][0]
            assert data["parent_source_ref"] == original["source_ref"]
            assert data["resource"]["format"] == "csv"
            response = download_client.get(data["downloadUrl"])
            assert response.status_code == 200
            assert [row["CID"] for row in csv.DictReader(io.StringIO(response.text))] == ["1", "2"]
            assert [name for name, _ in calls] == ["query_pubchem_compounds", "export_dataset"]
            assert not wrong_calls and len(files.requests) == 2
        finally:
            await service.close()
    asyncio.run(run())


@pytest.mark.parametrize("tool_name", ["molecule_search_compounds", "subset_records"])
def test_incompatible_existing_resource_call_is_corrected_before_dispatch(engine, files, monkeypatch, tool_name):
    calls = capture_dispatches(monkeypatch)

    async def run():
        gateway, wrong_calls = competing_gateway(tool_name)
        await warm(gateway)
        service = DatasetQA(engine, BareDialogue(), gateway)
        handle = None
        try:
            sid = session(service)
            original = await retrieve(service, sid)

            def wrong(messages, definitions):
                nonlocal handle
                handle = json.loads(messages[1].content)["published_artifacts"]["items"][0]["handle"]
                alias = next(item["function"]["name"] for item in definitions
                    if item["function"]["name"].endswith("_"+tool_name))
                return action(alias, dataset_path="dataset/invented.csv", **{OBJECT: handle,
                    TASK: {"complete_request": True, "operation": "export", "output_format": "csv"}})

            def correct(messages, definitions):
                assert not wrong_calls
                assert [name for name, _ in calls] == ["query_pubchem_compounds"]
                assert "invalid_parameters" in messages[-1].content
                return export_action(definitions, handle)

            service.dialogue = BareDialogue(wrong, correct, text())
            events = await collect(service, sid, "把这些记录保存成 CSV", rid="corrected-export")
            assert not payload(service, sid, events).get("error")
            data = result_cards(events)[0]["data"]["items"][0]
            assert data["parent_source_ref"] == original["source_ref"]
            assert [name for name, _ in calls] == ["query_pubchem_compounds", "export_dataset"]
            assert not wrong_calls and len(files.requests) == 2
        finally:
            await service.close()
    asyncio.run(run())


def test_deferred_format_mismatch_repairs_only_consumer_without_requery(engine, files, monkeypatch):
    calls = capture_dispatches(monkeypatch)

    async def run():
        gateway = MCPGateway({"piflow-corpus": Server(mcp)})
        await warm(gateway)
        service = DatasetQA(engine, BareDialogue(), gateway)
        workflow = compact_plan()
        workflow["steps"][-1].update(operation="export", output_format="csv", arguments={},
            inputs={"format": {"step": "query", "path": "/resource/format"}})

        def correct(messages, definitions):
            assert [name for name, _ in calls] == ["query_pubchem_compounds"]
            assert "invalid_parameters" in messages[-1].content
            shown = json.loads(messages[1].content)["plan"]
            assert shown["step_status"]["query"] == "succeeded"
            fixed = deepcopy(shown["editable"])
            fixed["steps"][-1].update(arguments={"format": "csv"}, inputs={})
            return action("remember", plan=fixed)

        try:
            sid = session(service)
            service.dialogue = BareDialogue(action("remember", plan=workflow), approve, correct, approve, text())
            events = await collect(service, sid, "从 PubChem 找化合物，导出 CSV")
            saved = payload(service, sid, events)
            assert not saved.get("error")
            assert saved["plan"]["revision"] == 2
            assert result_cards(events)[0]["data"]["items"][0]["resource"]["format"] == "csv"
            assert [name for name, _ in calls] == ["query_pubchem_compounds", "export_dataset"]
            assert len(files.requests) == 2
        finally:
            await service.close()
    asyncio.run(run())


def test_registered_export_goal_cannot_be_bypassed_by_omitting_resource_metadata(engine, files, monkeypatch):
    calls = capture_dispatches(monkeypatch)

    async def run():
        gateway, wrong_calls = competing_gateway("subset_records")
        await warm(gateway)
        service = DatasetQA(engine, BareDialogue(), gateway)
        handle = None
        try:
            sid = session(service)
            await retrieve(service, sid)

            def declare(messages, definitions):
                nonlocal handle
                handle = json.loads(messages[1].content)["published_artifacts"]["items"][0]["handle"]
                return action("remember", goals=[{"description": "导出已经取得的记录为 CSV",
                    "tool": "export_dataset", "object": handle, "operation": "export", "output_format": "csv"}])

            def wrong(messages, definitions):
                alias = next(item["function"]["name"] for item in definitions
                    if item["function"]["name"].endswith("_subset_records"))
                return action(alias, dataset_path="dataset/invented.csv")

            def correct(messages, definitions):
                assert not wrong_calls
                assert [name for name, _ in calls] == ["query_pubchem_compounds"]
                assert "invalid_parameters" in messages[-1].content
                return export_action(definitions, handle)

            service.dialogue = BareDialogue(declare, wrong, correct, text())
            events = await collect(service, sid, "把这些记录保存成 CSV", rid="declared-export")
            assert not payload(service, sid, events).get("error")
            assert result_cards(events)[0]["data"]["items"][0]["resource"]["format"] == "csv"
            assert [name for name, _ in calls] == ["query_pubchem_compounds", "export_dataset"]
            assert not wrong_calls and len(files.requests) == 2
        finally:
            await service.close()
    asyncio.run(run())


def test_changed_conditions_query_again_then_explicit_old_handle_exports_old_records(engine, files, monkeypatch):
    calls = capture_dispatches(monkeypatch)

    async def run():
        gateway = MCPGateway({"piflow-corpus": Server(mcp)})
        await warm(gateway)
        service = DatasetQA(engine, BareDialogue(), gateway)
        try:
            sid = session(service)
            old = await retrieve(service, sid)
            old_handle = service.artifacts.recent("alice")[0]["handle"]
            new = await retrieve(service, sid, threshold=90, limit=1, rid="changed")
            assert old["source_ref"] != new["source_ref"]
            assert [args["similarity_threshold"] for _, args in calls] == [80, 90]
            assert [args["limit"] for _, args in calls] == [1000, 1]

            def export_old(messages, definitions):
                state = json.loads(messages[1].content)
                assert state["published_artifacts"]["items"][0]["handle"] != old_handle
                assert len(state["available_artifacts"]) == 2
                return export_action(definitions, old_handle)

            service.dialogue = BareDialogue(export_old, text())
            events = await collect(service, sid, "把第一次找到的记录保存为 CSV", rid="old-export")
            assert not payload(service, sid, events).get("error")
            data = result_cards(events)[0]["data"]["items"][0]
            assert data["parent_source_ref"] == old["source_ref"]
            assert data["record_count"] == old["record_count"] == 2
            assert new["record_count"] == 1
            assert [name for name, _ in calls] == ["query_pubchem_compounds", "query_pubchem_compounds", "export_dataset"]
            assert len(files.requests) == 4
        finally:
            await service.close()
    asyncio.run(run())


def test_multiple_delivered_resources_keep_distinct_sources_for_followup(engine, files, monkeypatch):
    calls = capture_dispatches(monkeypatch)

    async def run():
        gateway = MCPGateway({"piflow-corpus": Server(mcp)})
        await warm(gateway)
        service = DatasetQA(engine, BareDialogue(), gateway)
        workflow = {"steps": [
            {"key": "first", "tool": "query_pubchem_compounds", "arguments": query_args(limit=1)},
            {"key": "second", "tool": "query_pubchem_compounds",
             "arguments": query_args(similarity_threshold=90, limit=1000)}]}
        selected = {}
        try:
            sid = session(service)
            service.dialogue = BareDialogue(action("remember", plan=workflow), approve, text())
            events = await collect(service, sid, "从 PubChem 按两个条件各找一批化合物", rid="two-sources")
            assert not payload(service, sid, events).get("error")

            def choose(messages, definitions):
                resources = json.loads(messages[1].content)["published_artifacts"]
                assert resources["total"] == len(resources["items"]) == 2
                assert len({item["handle"] for item in resources["items"]}) == 2
                chosen = max(resources["items"], key=lambda item: item["record_count"])
                selected.update(service.artifacts.get("alice", chosen["handle"])["resource"])
                return export_action(definitions, chosen["handle"])

            service.dialogue = BareDialogue(choose, text())
            events = await collect(service, sid, "把这两份里记录更多的一份保存成 CSV", rid="chosen-export")
            assert not payload(service, sid, events).get("error")
            data = result_cards(events)[0]["data"]["items"][0]
            assert data["parent_source_ref"] == selected["source_ref"]
            assert data["record_count"] == selected["record_count"] == 2
            assert [name for name, _ in calls] == ["query_pubchem_compounds", "query_pubchem_compounds", "export_dataset"]
            assert len(files.requests) == 4
        finally:
            await service.close()
    asyncio.run(run())
