"""Shared QA runtime integration: source-backed follow-ups, no custom planner."""
import asyncio

from mcp_servers import bdbe_mcp
from mcp_servers.corpus_mcp import mcp

from ..capabilities import TASK
from ..contracts import Server
from ..mcp import MCPGateway
from ..service import DatasetQA
from .test_bdbe_contracts import row
from .test_bdbe_files import upstream, GBFF
from .test_dataset_qa import collect, engine, remote, result_cards, session
from .test_decisions import BareDialogue, text
from .test_file_pipeline import files
from .test_local_artifacts import download_client


def test_search_detail_download_followups_with_real_mcp(engine, files, upstream, download_client, monkeypatch):
    calls = []
    def search(**kw):
        calls.append(("search", kw))
        return {"results": [row(Accession="NC_000001")], "total": 1}
    def detail(**kw):
        calls.append(("detail", kw))
        return row(Accession="NC_000001")
    monkeypatch.setattr(bdbe_mcp, "query_metadata", search)
    monkeypatch.setattr(bdbe_mcp, "get_metadata_detail", detail)
    async def run():
        dialogue = BareDialogue(
            remote("search_bdbe_metadata", term="ngs", **{TASK: {"complete_request": True,
                "keywords": ["ngs", "genome sequencing", "next generation sequencing", "sequencing metadata"],
                "original_keywords": ["ngs"]}}), text("找到一个候选。"),
            remote("get_bdbe_metadata_detail", **{TASK: {"complete_request": True}}), text("已取得详情。"),
            remote("download_bdbe_genbank", **{TASK: {"complete_request": True,
                "operation": "download", "output_format": "gbff"}}), text("文件已准备好。"))
        service = DatasetQA(engine, dialogue, MCPGateway({"piflow-corpus": Server(mcp)}))
        try:
            sid = session(service)
            first = await collect(service, sid, "在 BDBE 找 ngs 相关的数据", "search")
            cards = result_cards(first)
            assert len(cards) == 1
            assert cards[0]["data"]["items"][0]["source"] == "BDBE"
            second = await collect(service, sid, "查看这个记录的详情", "detail", result_id=cards[0]["result_id"])
            details = result_cards(second)
            assert details
            third = await collect(service, sid, "下载这个记录的 GenBank 文件", "download", result_id=details[0]["result_id"])
            assert result_cards(third)
            stored = service.artifacts.recent("alice")
            assert len(stored) == 1 and stored[0]["kind"] == "file"
            manifest = service.artifacts.get("alice", stored[0]["handle"])
            assert download_client.get(manifest["resource"]["downloadUrl"]).content == GBFF
            assert len(dialogue.inputs) == 6
            assert [kind for kind, _ in calls] == ["search"]*4+["detail"]
            assert calls[-1][1]["db"] == "BIE" and calls[-1][1]["sdi"] == "BIE-1"
            assert len(upstream.calls) == 1
        finally:
            await service.close()
    asyncio.run(run())


def test_explicit_accession_batch_uses_one_download_call(engine, files, upstream, download_client):
    async def run():
        dialogue = BareDialogue(
            remote("download_bdbe_genbank", dataids=["NC_000001", "NC_000002"],
                **{TASK: {"complete_request": True, "operation": "download", "output_format": "gbff"}}),
            text("已准备好 GenBank 文件。"))
        service = DatasetQA(engine, dialogue, MCPGateway({"piflow-corpus": Server(mcp)}))
        try:
            values = await collect(service, session(service), "从 BDBE 下载 NC_000001、NC_000002 的 GenBank 文件")
            cards = result_cards(values)
            assert len(cards) == 1
            assert len(upstream.calls) == 1
            assert upstream.calls[0]["dataids"] == "NC_000001,NC_000002"
            saved = service.artifacts.recent("alice")
            assert len(saved) == 1
            result = service.artifacts.get("alice", saved[0]["handle"])
            assert download_client.get(result["resource"]["downloadUrl"]).content == GBFF
            assert len(dialogue.inputs) == 2
        finally:
            await service.close()
    asyncio.run(run())
