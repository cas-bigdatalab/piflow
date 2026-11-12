"""Durable owned-file lookup, concurrent registration and bounded model context."""
import asyncio
import base64
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from hashlib import sha256
import json
import threading
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from pydantic import ValidationError
from langchain_core.messages import ToolMessage
from sqlalchemy import create_engine, event

from .. import artifacts as module
from ..artifacts import Artifacts, ArtifactSpec
from ..capabilities import OBJECT, TASK
from ..contracts import Limits, QAError, Server
from ..dialogue import Dialogue, FindArtifacts, Read, builtin_definitions
from ..execution import Execution
from ..mcp import MCPGateway
from ..persistence import Store
from ..service import DatasetQA
from .test_context_budget import cost
from .test_dataset_qa import action, collect, engine, result_cards, session
from .test_decisions import BareDialogue, text
from .test_file_pipeline import files, mcp, run_query, query_args


TOOL = SimpleNamespace(server="files", name="export")


def register(registry, key, *, user="alice", name=None, stamp=100, format="csv", version=1):
    card = {"result_id": "result-"+str(key), "data": {"query": {"version": version}, "resource": {
        "source_ref": "ref-"+str(key), "name": name or f"file-{key}.{format}", "format": format,
        "record_count": 1, "fields": ["value"], "sha256": sha256(str(key).encode()).hexdigest()}}}
    with patch.object(module, "time", SimpleNamespace(time=lambda: stamp)):
        return registry.register(user, "source-session", card, TOOL, ArtifactSpec())


def test_registration_is_atomic_across_service_instances_and_keeps_newer_metadata(tmp_path):
    database = create_engine("sqlite:///"+str(tmp_path/"artifacts.sqlite"))
    registries = [Artifacts(Store(database)) for _ in range(2)]
    barrier = threading.Barrier(2)
    def align_inserts(conn, cursor, statement, parameters, context, executemany):
        if statement.startswith("INSERT INTO dataset_qa_file_artifacts"):
            barrier.wait(timeout=10)
    event.listen(database, "before_cursor_execute", align_inserts)
    card = {"result_id": "result", "data": {"resource": {"source_ref": "shared", "format": "csv",
        "record_count": 1, "sha256": "0"*64}}}
    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            ids = list(pool.map(lambda registry: registry.register("alice", "sid", card, TOOL, ArtifactSpec()), registries))
        assert ids[0] == ids[1] and len(registries[0].recent("alice")) == 1
    finally:
        event.remove(database, "before_cursor_execute", align_inserts)
    try:
        aid = register(registries[0], "versioned", stamp=300, version=3)
        assert register(registries[1], "versioned", stamp=200, version=2) == aid
        assert registries[1].get("alice", aid)["provenance"]["query"] == {"version": 3}
        register(registries[1], "versioned", stamp=400, version=4)
        assert registries[0].get("alice", aid)["provenance"]["query"] == {"version": 4}
    finally:
        database.dispose()


def test_catalogue_pages_all_owned_files_with_ties_and_concurrent_inserts(engine):
    registry = Artifacts(Store(engine))
    expected = {register(registry, i, stamp=100+i//3) for i in range(23)}
    register(registry, "foreign", user="bob", stamp=500)
    assert len(registry.recent("alice")) == 10
    first = registry.find("alice", limit=3)
    seen = [row["handle"] for row in first["items"]]
    register(registry, "new-arrival", stamp=600)
    page = first
    while page.get("next_cursor"):
        page = registry.find("alice", cursor=page["next_cursor"], limit=3)
        seen.extend(row["handle"] for row in page["items"])
    assert set(seen) == expected and len(seen) == len(expected)
    assert registry.find("nobody")["items"] == []
    with pytest.raises(QAError):
        registry.find("bob", cursor=first["next_cursor"])
    with pytest.raises(QAError):
        registry.find("alice", query="changed", cursor=first["next_cursor"])


def test_catalogue_filters_use_actual_metadata_and_literal_names(engine):
    registry = Artifacts(Store(engine))
    target = register(registry, "target", name="100%_观测.csv", stamp=200)
    register(registry, "other", name="100X观测.csv", stamp=200)
    register(registry, "old", name="100%_观测.csv", stamp=100, format="jsonl")
    page = registry.find("alice", query="%_", source="files", format="CSV",
        updated_after=datetime.fromtimestamp(200, timezone.utc), updated_before=datetime.fromtimestamp(201, timezone.utc))
    assert [row["handle"] for row in page["items"]] == [target]
    assert registry.find("alice", query=target)["items"][0]["criteria"] == {"version": 1}
    assert registry.find("alice", query="100%_观测.csv")["items"]  # Multiple versions remain separate candidates.
    assert len(registry.find("alice", query="100%_观测.csv")["items"]) == 2


@pytest.mark.parametrize("cursor", ["garbage", "e30=", "W10=", "WzEsMiwzXQ==",
    base64.urlsafe_b64encode(json.dumps([10**310, "artifact", "scope"]).encode()).decode()])
def test_invalid_catalogue_cursor_is_controlled_feedback(engine, cursor):
    with pytest.raises(QAError) as caught:
        Artifacts(Store(engine)).find("alice", cursor=cursor)
    assert caught.value.code == "invalid_parameters"


@pytest.mark.parametrize("values", [{"limit": 6}, {"updated_after": "2026-11-01T00:00:00"},
    {"updated_after": "2026-11-02T00:00:00Z", "updated_before": "2026-11-01T00:00:00Z"}])
def test_catalogue_rejects_unbounded_pages_and_ambiguous_times(values):
    with pytest.raises(ValidationError):
        FindArtifacts.model_validate(values)


def test_context_pressure_retains_lookup_entrypoint_and_selected_source():
    dialogue = Dialogue(model=object())
    protected = {"artifact_catalog": {"tool": "find_artifacts", "guidance": "Recent files may be incomplete."},
        "references": {"current": {"handle": "current", "result_id": "owned-resource", "path": "", "kind": "object"}}}
    definitions = builtin_definitions(artifacts=True)
    minimal = dialogue.messages("Reuse the selected file", protected)
    dialogue.limits = Limits(working_chars=cost(minimal, definitions)+100)
    context = {**protected, "available_artifacts": [{"handle": "artifact-"+str(i).zfill(40),
        "name": "old-results.csv", "fields": ["value"]} for i in range(20)]}
    bounded = dialogue.budget(dialogue.messages("Reuse the selected file", context), definitions)
    loaded = json.loads(bounded[1].content)
    assert loaded["references"] == protected["references"]
    assert loaded["artifact_catalog"] == protected["artifact_catalog"]
    assert len(loaded.get("available_artifacts", [])) < 20
    assert any(item["function"]["name"] == "find_artifacts" for item in definitions)
    assert all(item["function"]["name"] != "find_artifacts" for item in builtin_definitions())
    assert dialogue.input_size(bounded, definitions) <= dialogue.input_budget


def test_catalogue_clipped_page_can_be_read_without_execution_or_focus_change(engine):
    async def run():
        service = DatasetQA(engine, BareDialogue(), MCPGateway({}))
        try:
            for index in range(6):
                register(service.artifacts, index, name="observation-"+str(index)+"x"*200, stamp=100+index)
            sid = session(service)
            task, _ = service.store.submit("alice", sid, "lookup", {"message": "Find saved files"}, None, service.owner)
            execution, context = Execution(), {"references": {}}
            receipt = await service._builtin("alice", sid, task["id"], "find_artifacts", {}, None, context)
            dialogue = Dialogue(model=object(), limits=Limits(result_chars=600))
            messages = dialogue.messages("Find saved files", {})
            request = action("find_artifacts")
            messages.extend([request, ToolMessage(name="find_artifacts", tool_call_id=request.tool_calls[0]["id"],
                content=json.dumps(receipt))])
            bounded = dialogue.budget(messages, builtin_definitions(artifacts=True))
            shown = json.loads(bounded[-1].content)
            assert shown["truncated"] and shown["result_id"] == receipt["result_id"]
            page = await service._read_result("alice", sid, Read(result_id=receipt["result_id"], path="/items", offset=4, limit=1))
            assert page["data"] == [receipt["data"]["items"][4]]
            assert context == {"references": {}} and not execution.cards and not execution.operations.items
            assert execution.observe("a", receipt, "find_artifacts")
            assert not execution.observe("b", {**receipt, "result_id": "another"}, "find_artifacts")
        finally:
            await service.close()
    asyncio.run(run())


def test_older_artifact_found_selected_and_exported_after_service_rebuild(engine, files):
    async def run():
        service = DatasetQA(engine, BareDialogue(), MCPGateway({"piflow-corpus": Server(mcp)}))
        old_sid = session(service)
        native = SimpleNamespace(server="piflow-corpus", name="query_pubchem_compounds")
        for index in range(13):
            data = run_query(query_args(limit=1), user="alice", request=f"archive-{index}")
            data["resource"]["name"] = f"archive-{index}.jsonl"
            service.artifacts.register("alice", old_sid, {"result_id": f"result-{index}", "data": data}, native, ArtifactSpec())
        await service.close()
        source_calls = len(files.requests)
        captured = {}
        def find(messages, definitions):
            loaded = json.loads(messages[1].content)
            assert "archive-0.jsonl" not in {row.get("name") for row in loaded["available_artifacts"]}
            assert "find_artifacts" in {item["function"]["name"] for item in definitions}
            return action("find_artifacts", query="archive-0.jsonl")
        def select(messages, definitions):
            receipt = json.loads(messages[-1].content)
            assert receipt["executed"] is False and len(receipt["data"]["items"]) == 1
            captured.update(receipt)
            return action("remember", focus=receipt["data"]["items"][0]["handle"])
        def export(messages, definitions):
            assert json.loads(messages[1].content)["references"]["current"]["value"]["name"] == "archive-0.jsonl"
            alias = next(item["function"]["name"] for item in definitions if item["function"]["name"].endswith("_export_dataset"))
            return action(alias, format="csv", **{OBJECT: "current", TASK: {"complete_request": True}})
        service = DatasetQA(engine, BareDialogue(find, select, export, text()), MCPGateway({"piflow-corpus": Server(mcp)}))
        try:
            sid = session(service, request="reopened")
            events = await collect(service, sid, "把 archive-0.jsonl 导出为 CSV")
            cards = result_cards(events)
            assert len(cards) == 1 and cards[0]["data"]["items"][0]["resource"]["format"] == "csv"
            assert len(files.requests) == source_calls and events[-1]["status"] == "COMPLETED"
            saved = service.store.selected_results("alice", sid, [captured["result_id"]])[0]
            assert saved["data"] == captured["data"]
            with pytest.raises(QAError):
                service.artifacts.get("bob", captured["data"]["items"][0]["handle"])
        finally:
            await service.close()
    asyncio.run(run())
