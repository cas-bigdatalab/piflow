"""Opt-in acceptance checks with real PubChem, MCP and downloads.

DATASET_QA_LIVE_PUBCHEM=1 runs the deterministic planner with real upstream I/O.
Also set DATASET_QA_LIVE_MODEL=1 to test the configured production model using its
normal credentials. Both modes use isolated temporary files and sessions.
"""
import asyncio
import csv
from copy import deepcopy
import hashlib
import io
import json
import os
import time

import httpx
import pytest

from ..contracts import Server
from ..dialogue import Dialogue
from ..mcp import MCPGateway, ToolSession
from ..service import DatasetQA
from .test_artifact_download_origin import http_mcp
from .test_dataset_qa import action, collect, engine, result_cards, session
from .test_decisions import BareDialogue, payload, text
from .test_planning import approve
from .test_workflow_input import compact_plan
from .test_followup_resource_execution import export_action


class LiveDialogue(Dialogue):
    """Count real model calls without substituting decisions or exposing secrets."""
    def __init__(self):
        super().__init__()
        self.model_calls = 0

    async def respond(self, messages, definitions):
        self.model_calls += 1
        async for chunk in super().respond(messages, definitions):
            yield chunk


@pytest.mark.skipif(os.getenv("DATASET_QA_LIVE_PUBCHEM") != "1", reason="Opt-in external PubChem test")
@pytest.mark.parametrize("planner", ["scripted", "model"])
def test_live_same_session_query_export_and_download(engine, tmp_path, monkeypatch, planner):
    if planner == "model" and os.getenv("DATASET_QA_LIVE_MODEL") != "1":
        pytest.skip("Production model acceptance requires explicit opt-in and configured credentials")
    monkeypatch.setenv("DATASET_QA_ARTIFACT_ROOT", str(tmp_path / "artifacts"))
    monkeypatch.delenv("DATASET_QA_ARTIFACT_BASE_URL", raising=False)
    monkeypatch.delenv("DATASET_QA_ARTIFACT_SIGNING_KEY", raising=False)
    calls = []
    original = ToolSession.call
    async def capture(tools, alias, arguments, **kwargs):
        calls.append((tools.loaded[alias].name, deepcopy(arguments)))
        return await original(tools, alias, arguments, **kwargs)
    monkeypatch.setattr(ToolSession, "call", capture)

    async def run():
        async with http_mcp("/api/piflow/v1/mcp") as base:
            service = DatasetQA(engine, BareDialogue(), MCPGateway({"piflow-corpus": Server(base + "/")}))
            sid = session(service)
            try:
                live = LiveDialogue() if planner == "model" else None
                for threshold, limit in [(80, 1000), (90, 100)]:
                    responses = [action("remember", plan=compact_plan(threshold, limit)), approve, text()]
                    if not calls:
                        responses.insert(0, action("load_mcp_tools", server="piflow-corpus"))
                    service.dialogue = live if live is not None else BareDialogue(*responses)
                    prior_model_calls = live.model_calls if live is not None else 0
                    started = time.perf_counter()
                    events = await collect(service, sid,
                        "我想从 PubChem 找一批和这个分子相似的化合物，用来做后续筛选，"
                        "SMILES 是 CC(=O)OC1=CC=CC=C1C(=O)O。"
                        f"相似度至少 {threshold}%，分子量在 100 到 500 之间，LogP 在 -1 到 5 之间，"
                        f"先帮我下载 {limit} 条，保存成 CSV。", rid=str(threshold))
                    saved = payload(service, sid, events)
                    assert not saved.get("error")
                    acceptance = saved["plan"]["acceptance"]
                    assert acceptance and all(item["state"] == "accepted" for item in acceptance.values())
                    assert len(saved["operations"]) == 2 and all(op["state"] == "succeeded" for op in saved["operations"])
                    cards = result_cards(events)
                    exports = [item for card in cards for item in card["data"]["items"]
                        if isinstance(item, dict) and item.get("resource", {}).get("format") == "csv"]
                    assert len(exports) == 1
                    output = exports[0]
                    assert output["resource"]["format"] == "csv"
                    assert output["downloadUrl"].startswith(base + "/artifacts/")
                    async with httpx.AsyncClient(timeout=20) as client:
                        response = await client.get(output["downloadUrl"])
                        partial = await client.get(output["downloadUrl"], headers={"Range": "bytes=0-15"})
                    assert response.status_code == 200 and partial.status_code == 206
                    assert "attachment" in response.headers["content-disposition"]
                    assert hashlib.sha256(response.content).hexdigest() == output["resource"]["sha256"]
                    rows = list(csv.DictReader(io.StringIO(response.text)))
                    assert 0 < len(rows) == output["record_count"] <= limit
                    assert len({r["CID"] for r in rows}) == len(rows)
                    assert all(100 <= float(r["MolecularWeight"]) <= 500 and -1 <= float(r["XLogP"]) <= 5 for r in rows)
                    print({"threshold": threshold, "target": limit, "rows": len(rows),
                        "seconds": round(time.perf_counter() - started, 2),
                        "planner": planner, "model_calls": live.model_calls - prior_model_calls if live is not None
                        else len(service.dialogue.inputs), "mcp_calls": 2, "http": [200, 206]})
                assert [name for name, _ in calls] == ["query_pubchem_compounds", "export_dataset"] * 2
                assert calls[0][1]["similarity_threshold"] == 80 and calls[0][1]["limit"] == 1000
                assert calls[2][1]["similarity_threshold"] == 90 and calls[2][1]["limit"] == 100
                assert calls[0][1]["smiles"] == calls[2][1]["smiles"] == "CC(=O)OC1=CC=CC=C1C(=O)O"
                for index in (0, 2):
                    rules = {rule["field"]: rule for rule in calls[index][1]["filters"]}
                    assert set(rules) == {"MolecularWeight", "XLogP"}
                    assert (rules["MolecularWeight"]["minimum"], rules["MolecularWeight"]["maximum"]) == (100, 500)
                    assert (rules["XLogP"]["minimum"], rules["XLogP"]["maximum"]) == (-1, 5)
                assert calls[1][1]["source_ref"] != calls[3][1]["source_ref"]
            finally:
                await service.close()
    asyncio.run(run())


@pytest.mark.skipif(os.getenv("DATASET_QA_LIVE_PUBCHEM") != "1", reason="Opt-in external PubChem test")
def test_live_registered_query_then_next_turn_export_keeps_original_records(engine, tmp_path, monkeypatch):
    monkeypatch.setenv("DATASET_QA_ARTIFACT_ROOT", str(tmp_path / "artifacts"))
    monkeypatch.delenv("DATASET_QA_ARTIFACT_BASE_URL", raising=False)
    monkeypatch.delenv("DATASET_QA_ARTIFACT_SIGNING_KEY", raising=False)
    calls = []
    original = ToolSession.call

    async def capture(tools, alias, arguments, **kwargs):
        calls.append((tools.loaded[alias].name, deepcopy(arguments)))
        return await original(tools, alias, arguments, **kwargs)
    monkeypatch.setattr(ToolSession, "call", capture)

    async def run():
        async with http_mcp("/api/piflow/v1/mcp") as base:
            query = compact_plan(90, 100)["steps"][0]
            dialogue = BareDialogue(action("load_mcp_tools", server="piflow-corpus"),
                action("remember", goals=[{"description": "Find the requested compounds", "tool": query["tool"]}]),
                action("remember", plan={"steps": [query]}), approve, text())
            service = DatasetQA(engine, dialogue, MCPGateway({"piflow-corpus": Server(base + "/")}))
            sid = session(service)
            try:
                events = await collect(service, sid,
                    "Find 100 PubChem compounds similar to SMILES CC(=O)OC1=CC=CC=C1C(=O)O, "
                    "similarity at least 90%, molecular weight 100 to 500 and LogP -1 to 5.", rid="query")
                saved = payload(service, sid, events)
                assert not saved.get("error") and len(saved["operations"]) == 1
                assert saved["plan"]["operations"] == {"query": "op1"}
                records = result_cards(events)[0]["data"]["items"][0]

                def export(messages, definitions):
                    resource = json.loads(messages[1].content)["published_artifacts"]["items"][0]
                    return export_action(definitions, resource["handle"])

                service.dialogue = BareDialogue(export, text())
                exported = await collect(service, sid, "Save these records as CSV", rid="export")
                assert not payload(service, sid, exported).get("error")
                output = result_cards(exported)[0]["data"]["items"][0]
                assert output["parent_source_ref"] == records["resource"]["source_ref"]
                assert output["resource"]["format"] == "csv"
                async with httpx.AsyncClient(timeout=20) as client:
                    downloaded = await client.get(output["downloadUrl"])
                assert downloaded.status_code == 200
                assert hashlib.sha256(downloaded.content).hexdigest() == output["resource"]["sha256"]
                assert len(list(csv.DictReader(io.StringIO(downloaded.text)))) == output["record_count"]
                assert [name for name, _ in calls] == ["query_pubchem_compounds", "export_dataset"]
                assert len(dialogue.inputs) == 5 and len(service.dialogue.inputs) == 2
                print({"flow": "registered query then next-turn CSV", "rows": output["record_count"],
                    "mcp_calls": len(calls), "http": 200, "same_source": True})
            finally:
                await service.close()
    asyncio.run(run())
