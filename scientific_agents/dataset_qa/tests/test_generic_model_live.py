"""Opt-in real-model checks with multiple in-process MCPs and controlled records.

These fixtures exercise routing/decisions, not external archive availability.
They use DATASET_QA_LIVE_SEQUENCE and the same credential handling as sequence tests.
"""
import asyncio
from copy import deepcopy
import json
import logging
import os

from fastmcp import Client, FastMCP
import pytest

from ..contracts import Server
from ..execution import Execution
from ..mcp import MCPGateway
from ..search import normalize_keyword
from ..service import DatasetQA
from .test_dataset_qa import collect, engine, result_cards, session
from .test_decisions import payload
from .test_model_sequence_live import AcceptanceFailure, ObservedDialogue, require


ARCHIVES = {
    "OceanArchive": ("Coastal ocean and marine sensor observations", ["ocean", "marine", "海洋"]),
    "ForestArchive": ("Forest carbon flux and ecological observations", ["forest", "carbon", "森林", "碳"]),
    "MaterialArchive": ("Materials properties and laboratory measurements", ["materials", "laboratory", "材料"]),
}


def archive_service(source, description, terms, calls):
    server = FastMCP(source)
    rows = [{"id": source+"-"+str(index), "title": description+" "+str(index),
        "description": "Controlled test records with measurement fields and a stable identifier."}
        for index in range(1, 7)]
    readonly = {"readOnlyHint": True, "idempotentHint": True}

    def metadata(label, operation, **qa):
        return {"piflow": {"view_type": "table" if operation != "detail" else "detail", "qa": {
            "label": label, "routing": {"group": "catalogue", "source": source, "operations": [operation]}, **qa}}}

    @server.tool(annotations=readonly, meta=metadata("数据集检索", "search", collection="/items", search={
        "query": "term", "page": "page", "page_size": "size", "total": "/total", "identity": ["/id"]}))
    async def find_records(term: str, page: int = 1, size: int = 5) -> dict:
        """Search this archive's datasets by subject; return candidate records and total."""
        calls.append((source, "find_records", {"term": term, "page": page, "size": size}))
        matches = rows if any(word in term.casefold() for word in terms) else []
        return {"items": deepcopy(matches[(page-1)*size:page*size]), "total": len(matches)}

    @server.tool(annotations=readonly, meta=metadata("数据集详情", "detail", atomic=True,
        bind={"record_id": ["/id"]}, object=""))
    async def describe_record(record_id: str) -> dict:
        """Read one dataset's metadata using its returned record identifier."""
        calls.append((source, "describe_record", {"record_id": record_id}))
        return deepcopy(next(row for row in rows if row["id"] == record_id))

    @server.tool(annotations=readonly, meta=metadata("目录结构", "directory", atomic=True,
        bind={"record_id": ["/id"]}))
    async def list_files(record_id: str) -> dict:
        """Read the root directory of one dataset using its returned identifier."""
        calls.append((source, "list_files", {"record_id": record_id}))
        require(any(row["id"] == record_id for row in rows), "Directory received an ungrounded identifier")
        return {"files": [{"name": "measurements.jsonl", "is_file": True}, {"name": "notes.txt", "is_file": True}]}

    return server


@pytest.mark.parametrize("source", list(ARCHIVES))
def test_multi_archive_fixture_preserves_native_schemas_and_bound_record_ids(source):
    async def run():
        calls = []
        description, terms = ARCHIVES[source]
        server = archive_service(source, description, terms, calls)
        gateway = MCPGateway({source: Server(source, description)}, client_factory=lambda *a, **kw: Client(server))
        async with gateway.session() as tools:
            await tools.load(source)
            aliases = {tool.name: tool.alias for tool in tools.loaded.values()}
            for tool in tools.loaded.values():
                definition = tool.definition()["function"]
                # Aliases are opaque; identical remote names need an explicit
                # alias-to-authority map even before discovery history exists.
                assert definition["name"] == aliases[tool.name]
                assert "MCP service: "+source in definition["description"]
                assert "Data source: "+source in definition["description"]
                assert "Tool group: catalogue" in definition["description"]
            _, result = await tools.call(aliases["find_records"], {"term": terms[0]})
            assert result.data["total"] == 6 and len(result.data["items"]) == 5
            identifier = result.data["items"][1]["id"]
            for name in ("describe_record", "list_files"):
                _, result = await tools.call(aliases[name], {"record_id": identifier})
                assert result.data and calls[-1][2] == {"record_id": source+"-2"}
    asyncio.run(run())


@pytest.mark.skipif(os.getenv("DATASET_QA_LIVE_SEQUENCE") != "1", reason="Opt-in real model with controlled multi-server MCP data")
@pytest.mark.parametrize("warm,first,utterance,followup", [
    (False, "OceanArchive", "Find coastal ocean observations in OceanArchive.", "Show the second dataset's details and directory structure."),
    (True, "ForestArchive", "请在 ForestArchive 找森林碳通量观测相关的数据集。", "把第二项的详细信息和文件目录一起给我。"),
])
def test_real_model_routes_multiple_archives_and_preserves_each_requested_outcome(engine, monkeypatch, caplog, tmp_path,
        warm, first, utterance, followup):
    if os.getenv("API_KEY") and not os.getenv("LLM_API_KEY"):
        monkeypatch.setenv("LLM_API_KEY", os.environ["API_KEY"])
    caplog.set_level(logging.CRITICAL)
    calls, corrections, reports = [], [], []
    original = Execution.correct

    def correct(execution, error, limit, **kwargs):
        detail = error.detail if isinstance(error.detail, dict) else {}
        corrections.append({"code": error.code, **{key: detail.get(key)
            for key in ("origin", "phase", "dispatched")}})
        return original(execution, error, limit, **kwargs)

    monkeypatch.setattr(Execution, "correct", correct)

    async def run():
        servers = {name: archive_service(name, *spec, calls) for name, spec in ARCHIVES.items()}
        gateway = MCPGateway({name: Server(name, spec[0]) for name, spec in ARCHIVES.items()},
            client_factory=lambda name, **kwargs: Client(servers[name]))
        if warm:
            async with gateway.session() as tools:
                await tools.load("MaterialArchive")  # Irrelevant earlier cache must not dominate new intent.
        dialogue = ObservedDialogue()
        service = DatasetQA(engine, dialogue, gateway)
        sid = session(service)
        second = "ForestArchive" if first == "OceanArchive" else "OceanArchive"
        topic = "forest carbon" if second == "ForestArchive" else "coastal ocean"
        turns = [("search", first, utterance), ("combined", first, followup),
            ("switch", second, f"Now find {topic} observations in {second}."),
            ("directory", second, "Show the first dataset's directory only.")]
        try:
            for label, source, question in turns:
                begin, round_begin, correction_begin = len(calls), len(dialogue.rounds), len(corrections)
                events = await collect(service, sid, question, rid=label)
                actual = calls[begin:]
                rounds = len(dialogue.rounds)-round_begin
                reports.append({"turn": label, "source": source, "model_calls": rounds,
                    "mcp_calls": len(actual), "corrections": corrections[correction_begin:],
                    "fixture_calls": actual, "model_trace": dialogue.rounds[round_begin:]})
                require(events[-1].get("status") == "COMPLETED" and not events[-1].get("outcome"), "Requested outcomes were not delivered")
                require(actual and all(server == source for server, _, _ in actual), "A stale or unrelated archive was selected")
                cards = result_cards(events)
                if label in {"search", "switch"}:
                    require(all(name == "find_records" for _, name, _ in actual), "Search performed an unrequested operation")
                    require(normalize_keyword(actual[0][2]["term"]) in normalize_keyword(question), "Initial subject was not extracted from the current request")
                    require(len(actual) <= 4 and len(cards) == 1, "Search repeated work or lost its candidate list")
                else:
                    expected = {"describe_record", "list_files"} if label == "combined" else {"list_files"}
                    require({name for _, name, _ in actual} == expected and len(actual) == len(expected), "A requested read was omitted or repeated")
                    require(all(args["record_id"] == source+("-2" if label == "combined" else "-1") for _, _, args in actual), "Ordinal binding used a stale or wrong source")
                    require(len(cards) == len(expected), "Successful independent outcomes did not all reach display cards")
                require(not payload(service, sid, events).get("error"), "Execution retained an unresolved error")
                require(rounds <= (6 if label in {"search", "switch"} else 4), "Excess model decisions for a bounded request")
                repairs = corrections[correction_begin:]
                # A guarded object-selection repair is supported behavior. It
                # may add one decision, never a wrong or repeated MCP dispatch.
                require(len(repairs) <= 1 and all(item == {"code": "invalid_parameters",
                    "origin": "object_binding", "phase": "input_binding", "dispatched": False}
                    for item in repairs), "Unexpected correction or repeated object-selection repair")
        finally:
            await service.close()
            (tmp_path / "multi_archive_acceptance.json").write_text(
                json.dumps(reports, ensure_ascii=False, indent=2), encoding="utf-8")

    try:
        asyncio.run(run())
    except Exception as exc:
        detail = str(exc) if isinstance(exc, AcceptanceFailure) else type(exc).__name__
        pytest.fail("Multi-server acceptance: "+detail+"; report="+str(tmp_path / "multi_archive_acceptance.json"), pytrace=False)
    print("MULTI_SERVER_ACCEPTANCE "+json.dumps(reports, ensure_ascii=False))
