"""BDBE adapter contracts, without assuming a live upstream or model."""
import asyncio
import hashlib
import json
from copy import deepcopy
from types import SimpleNamespace

import pytest
from fastmcp import Client

from mcp_servers import bdbe_mcp
from mcp_servers.corpus_mcp import mcp
from services import bdbe_service as backend
from ...agent_profiles import AgentProfile, ToolScope
from ...pubchem.profile import PROFILE as PUBCHEM
from ..capabilities import inputs, profile, request_identifiers, same_object_identity
from ..contracts import QAError, Server
from ..mcp import MCPGateway
from ..routing import select_tools
from ..search import SearchRun


def row(db="BIE", sdi="BIE-1", **values):
    return {"db": db, "SDI": sdi, "Title": "Genome <high-light>study</high-light>",
        "Description": "Sequencing metadata", **values}


@pytest.mark.parametrize("envelope", [lambda rows: {"results": rows}, lambda rows: {"data": {"results": rows}}, lambda rows: rows])
def test_page_preserves_names_namespaces_and_raw_evidence(envelope):
    rows = [row(), row("OtherDB", "BIE-1", UID=44, Accession="NC_000001.11")]
    result = backend.metadata_page(envelope(deepcopy(rows)), pagesize=5)
    assert result["pagination"] == {"page": 1, "page_size": 5, "total": None}
    assert result["items"][0]["title"] == "Genome study"
    assert result["items"][0]["raw"] == rows[0]
    assert "accessions" not in result["items"][0]
    assert result["items"][1]["accessions"] == ["NC_000001.11"]


def test_aggregate_search_retains_each_records_real_database():
    result = backend.metadata_page({"results": [row(), row("OtherDB")]}, db="Aggregate")
    assert [item["db"] for item in result["items"]] == ["BIE", "OtherDB"]
    detail = backend.metadata_detail({"Title": "Metadata only", "UID": 44}, db="BIE", sdi="BIE-1")
    assert detail["item"]["db"] == "BIE" and detail["item"]["sdi"] == "BIE-1"
    assert detail["item"]["raw"] == {"Title": "Metadata only", "UID": 44}


@pytest.mark.parametrize("payload", [{"message": "try later"}, {"results": {}}, {"results": [None]},
    {"results": [{"message": "try later"}]}, {"results": [{"error": "denied"}]},
    {"code": 500, "results": []}, {"success": False, "results": []}, {"error": "denied", "results": []}])
def test_malformed_or_business_error_is_not_an_empty_success(payload):
    with pytest.raises(backend.BdbeUpstreamError):
        backend.metadata_page(payload)


def test_empty_results_unknown_totals_and_detail_binding():
    assert backend.metadata_page({"results": []})["items"] == []
    assert backend.metadata_page({"results": [], "count": 0})["pagination"]["total"] is None
    assert backend.metadata_page({"results": [], "total": "0"})["pagination"]["total"] == 0
    result = backend.metadata_detail({"data": row()}, db="BIE", sdi="BIE-1")
    assert result["item"]["sdi"] == "BIE-1"
    assert backend.metadata_detail([], db="BIE", sdi="BIE-1")["item"] is None
    for payload in [row("OtherDB"), row(sdi="other"), {"message": "unavailable"}, [row(), row()],
            {"data": {"message": "try later"}}, {"data": {"error": "denied"}}]:
        with pytest.raises(backend.BdbeUpstreamError):
            backend.metadata_detail(payload, db="BIE", sdi="BIE-1")


def test_upstream_transport_closes_responses_and_never_places_key_in_query(monkeypatch):
    response = SimpleNamespace(ok=True, json=lambda: {"results": []}, close=lambda: calls.append("closed"))
    calls = []
    def get(url, **kwargs):
        calls.append((url, kwargs))
        return response
    monkeypatch.setattr(backend.requests, "get", get)
    monkeypatch.setattr(backend, "_headers", lambda **kwargs: {"X-AK": "private-test-key"})
    backend.query_metadata(term="ngs", db="BIE", page=2, pagesize=3, genome_next="opaque", sessionid="upstream")
    assert calls[-1] == "closed"
    assert calls[0][1]["params"] == {"term": "ngs", "db": "BIE", "page": 2, "pagesize": 3, "genomeNext": "opaque"}
    assert "private-test-key" not in str(calls[0][1]["params"])
    response.ok, response.status_code = False, 401
    with pytest.raises(backend.BdbeUpstreamError) as caught:
        backend.query_metadata(term="ngs")
    assert caught.value.status_code == 401 and calls[-1] == "closed"


def test_real_mcp_schema_alias_and_normalized_result(monkeypatch):
    calls = []
    monkeypatch.setattr(bdbe_mcp, "query_metadata", lambda **kw: calls.append(kw) or {"results": [row()], "total": 1})
    async def run():
        async with Client(mcp) as client:
            value = await client.call_tool("search_bdbe_metadata", {"term": "ngs", "genomeNext": "token"})
            assert value.data["items"][0]["sdi"] == "BIE-1"
    asyncio.run(run())
    assert calls[0]["genome_next"] == "token" and calls[0]["pagesize"] == 20


def test_group_routing_binding_dedup_and_future_child_scope():
    async def run():
        gateway = MCPGateway({"piflow-corpus": Server(mcp)})
        async with gateway.session() as tools:
            all_tools = await tools.tools("piflow-corpus")
            for query, expected in [
                ("我想找共和县光伏观测站相关的数据集", {"search_corpus_datasets"}),
                ("看下这个数据集的详情以及目录结构", {"get_corpus_dataset_detail", "get_corpus_dataset_directory"}),
                ("从 PubChem 找相似化合物 SMILES 并保存成 CSV", {"query_pubchem_compounds", "export_dataset"}),
                ("在 BDBE 找 ngs 相关的数据", {"search_bdbe_metadata"}),
            ]:
                assert expected <= {tool.name for tool in select_tools(all_tools, query, source_scope=True)[:4]}
            # Loading an additional provider must retain the old plan identity.
            for tool in all_tools:
                if tool.name not in {"query_pubchem_compounds", "export_dataset"}:
                    continue
                legacy = profile(tool).model_dump(exclude={"label", "name_paths"})
                legacy["artifact"].pop("kind")
                body = {"schema": tool.schema, "annotations": {key: tool.annotations.get(key) for key in
                    ("readOnlyHint", "destructiveHint", "idempotentHint", "openWorldHint")}, "qa": legacy}
                expected = hashlib.sha256(json.dumps(body, sort_keys=True, ensure_ascii=False,
                    separators=(",", ":"), allow_nan=False).encode()).hexdigest()
                assert tool.plan_signature == expected
            scoped = select_tools(all_tools, "BDBE ngs", source_scope=True)
            assert all(profile(tool).routing.source in {"", "BDBE"} for tool in scoped)
            await tools.load("piflow-corpus", group="bdbe")
            loaded = {tool.name: tool for tool in tools.loaded.values()}
            assert set(loaded) == {"search_bdbe_metadata", "get_bdbe_metadata_detail", "download_bdbe_genbank"}
            detail, download = loaded["get_bdbe_metadata_detail"], loaded["download_bdbe_genbank"]
            assert request_identifiers(download, {"dataids": ["NC_1", "NC_2"]}, "下载 NC_1、NC_2") == {"dataids": ["NC_1", "NC_2"]}
            assert request_identifiers(download, {"dataids": ["NC_1", "invented"]}, "下载 NC_1、NC_2") == {}
            records = backend.metadata_page({"results": [row(), row("OtherDB")], "total": 2})["items"]
            assert inputs(detail, {}, records[0])["sdi"] == "BIE-1"
            assert not same_object_identity(detail, *records)
            with pytest.raises(QAError):
                inputs(detail, {}, {**records[0], "source": "corpus"})
            with pytest.raises(QAError):
                inputs(download, {}, records[0])
            selected = backend.metadata_page({"results": [row(Accession="NC_000001.11")]})["items"][0]
            assert inputs(download, {}, selected)["dataids"] == ["NC_000001.11"]
            desc = profile(loaded["search_bdbe_metadata"])
            search = SearchRun.create(desc.search, {"term": "ngs", "page": 1, "pagesize": 20}, ["ngs"])
            search.record({"items": records, "pagination": {"total": 2}}, desc.collection, "receipt")
            assert search.view()["unique_count"] == 2
        for agent, expected in [
            (PUBCHEM, {"query_pubchem_compounds", "export_dataset"}),
            (AgentProfile("example", "Scoped", tool_scope=(ToolScope("piflow-corpus", groups=("bdbe",)),)),
                {"search_bdbe_metadata", "get_bdbe_metadata_detail", "download_bdbe_genbank"}),
        ]:
            async with gateway.for_profile(agent).session() as tools:
                assert {t.name for t in await tools.tools("piflow-corpus")} == expected
    asyncio.run(run())
