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
                    assert saved["plan"]["acceptance"]["export"]["state"] == "accepted"
                    assert len(saved["operations"]) == 2
                    cards = result_cards(events)
                    assert len(cards) == 1
                    output = cards[0]["data"]["items"][0]
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
