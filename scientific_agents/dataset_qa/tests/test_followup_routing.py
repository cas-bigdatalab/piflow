"""Resource-aware recall stays bounded and does not lock users to an old source."""
import asyncio
from copy import deepcopy
import json
from types import SimpleNamespace

import pytest

from ..capabilities import validate_intent
from ..artifacts import ArtifactSpec
from ..contracts import Limits, QAError
from ..dialogue import Dialogue, builtin_definitions
from ..execution import Execution
from ..mcp import Tool, ToolSession
from ..results import ToolResult
from ..routing import select_tools
from ..service import DatasetQA
from .test_context_budget import cost, exchange
from .test_dataset_qa import Backend, action, collect, definition, engine
from .test_decisions import BareDialogue
from .test_published_artifacts import begin, publish, save


RESOURCES = [{"handle": "artifact-"+"a"*40, "result_id": "previous:0", "server": "tools",
    "kind": "record_resource", "format": "jsonl", "record_count": 1000}]


def backend_catalogue():
    backend = Backend()
    competitors = []
    for index in range(10):
        item = definition("process_"+str(index), {"dataset_path": {"type": "string"}}, ["dataset_path"])
        item.description = "save these records csv local structure filtering"
        item.meta = {"piflow": {"qa": {"routing": {"group": "local", "source": "local",
            "operations": ["filter"], "inputs": ["workspace_path"], "outputs": ["csv"]}}}}
        competitors.append(item)
    exporter = definition("materialize_records", {"source_ref": {"type": "string"},
        "format": {"type": "string", "enum": ["csv", "jsonl"], "default": "csv"}}, ["source_ref"])
    exporter.description = "Materialize an owned reference"
    exporter.meta = {"piflow": {"qa": {"atomic": True, "bind": {"source_ref": ["/source_ref"]},
        "artifact": {"consume": "source_ref"},
        "result": {"kind": "exported_file", "argument_paths": {"format": "/resource/format"}},
        "routing": {"group": "conversion", "operations": ["export"],
            "inputs": ["record_resource"], "outputs": ["csv", "jsonl"]}}}}
    new_query = definition("new_observations", {"query": {"type": "string"}}, ["query"])
    new_query.description = "Search NewDB latest observations"
    new_query.meta = {"piflow": {"qa": {"routing": {"group": "observations", "source": "NewDB",
        "operations": ["query"], "outputs": ["records"]}}}}
    legacy = definition("legacy_echo", {"reference": {"type": "string"}}, ["reference"])
    backend.catalog = {"tools": [*competitors, exporter, new_query, legacy]}
    return backend


def test_cold_and_warm_discovery_recall_consumer_without_extra_business_calls():
    async def run():
        backend = backend_catalogue()
        gateway = backend.gateway()
        for warm in (False, True):
            async with gateway.session() as tools:
                await tools.prepare("save these records csv", resources=RESOURCES)
                names = [tool.name for tool in tools.loaded.values()]
                assert names[0] == "process_0"  # Relevance is preserved, not silently overridden.
                assert names[1] == "materialize_records"
                assert len(names) <= 4
                if warm:
                    assert not tools.clients
        assert backend.lists == ["tools"]
        assert not backend.calls
    asyncio.run(run())


def test_explicit_new_source_remains_first_with_previous_resource_available():
    async def run():
        backend = backend_catalogue()
        async with backend.gateway().session() as tools:
            await tools.prepare("Search NewDB latest observations", resources=RESOURCES)
            names = [tool.name for tool in tools.loaded.values()]
            assert names[:2] == ["new_observations", "materialize_records"]
            assert tools.request_resources == tuple(RESOURCES)
    asyncio.run(run())


def test_wrong_authority_does_not_promote_resource_consumer():
    async def run():
        backend = backend_catalogue()
        async with backend.gateway().session() as tools:
            catalogue = await tools.tools("tools")
            ordinary = select_tools(catalogue, "save these records csv")
            wrong_owner = select_tools(catalogue, "save these records csv",
                resources=[{**RESOURCES[0], "server": "another-service"}])
            assert ordinary == wrong_owner
            assert "materialize_records" not in [tool.name for tool in wrong_owner[:4]]
    asyncio.run(run())


def test_resource_recall_preserves_explicit_groups_and_catalogue_pagination():
    async def run():
        backend = backend_catalogue()
        async with backend.gateway().session() as tools:
            await tools.prepare("save these records csv", resources=RESOURCES)
            page = await tools.load("tools", group="local", limit=3)
            assert all(item["tool"].startswith("process_") for item in page["items"])
            seen, offset = [], 0
            while True:
                page = await tools.load("tools", offset=offset, limit=3)
                seen.extend(item["tool"] for item in page["items"])
                if "next_offset" not in page:
                    break
                offset = page["next_offset"]
            assert len(seen) == len(set(seen)) == len(backend.catalog["tools"])
            assert set(seen) == {item.name for item in backend.catalog["tools"]}
            assert seen[1] == "materialize_records"
    asyncio.run(run())


def test_unknown_contract_preserves_ordinary_legacy_calls():
    async def run():
        backend = backend_catalogue()
        async with backend.gateway().session() as tools:
            await tools.prepare("legacy_echo", resources=RESOURCES)
            tool = next(tool for tool in tools.loaded.values() if tool.name == "legacy_echo")
            validate_intent(tool, None, {"reference": "user-supplied-value"})
            result = await tools.call(tool.alias, {"reference": "user-supplied-value"})
            assert result[1].data["reference"] == "user-supplied-value"
        assert backend.calls == [("tools", "legacy_echo", {"reference": "user-supplied-value"})]
    asyncio.run(run())


@pytest.mark.parametrize("with_exchange", [False, True])
def test_published_artifact_identity_survives_budget_pressure_and_tool_exchange(with_exchange):
    manifest = {"items": deepcopy(RESOURCES), "total": 1, "guidance": "Select a saved handle for reuse."}
    protected = {"published_artifacts": manifest,
        "artifact_catalog": {"tool": "find_artifacts", "guidance": "Find older owned results."}}
    dialogue = Dialogue(model=object())
    definitions = builtin_definitions(artifacts=True)
    calls = exchange({"saved": True}, name="remember") if with_exchange else []
    minimal = dialogue.messages("Save these records as CSV", protected)+calls
    dialogue.limits = Limits(working_chars=cost(minimal, definitions)+100)
    context = {**protected,
        "published_results": {"items": [{"result_id": "previous:0", "data": "historical preview "*1000}]},
        "available_artifacts": [{"handle": "artifact-"+str(i).zfill(40), "name": "unrelated.csv"} for i in range(50)]}
    messages = dialogue.messages("Save these records as CSV", context)+calls
    bounded = dialogue.budget(messages, definitions)
    loaded = json.loads(bounded[1].content)
    assert loaded["published_artifacts"] == manifest
    assert loaded["artifact_catalog"] == protected["artifact_catalog"]
    assert len(loaded.get("available_artifacts", [])) < 50
    assert dialogue.input_size(bounded, definitions) <= dialogue.input_budget
    assert json.loads(messages[1].content)["published_artifacts"] == manifest


def test_service_memory_updates_preserve_actual_delivered_file_candidates(engine):
    async def run():
        captured = {}
        def remember_format(messages, definitions):
            context = json.loads(messages[1].content)
            captured.update(deepcopy(context["published_artifacts"]))
            assert captured["total"] == len(captured["items"]) == 2
            return action("remember", values={"requested_format": "CSV"})
        def clarify_source(messages, definitions):
            context = json.loads(messages[1].content)
            assert context["published_artifacts"] == captured
            assert context["memory"]["requested_format"] == "CSV"
            return action("request_input", missing="选择需要导出的记录集合", question="要保存哪一份记录？",
                options=["第一份", "第二份"])
        backend = backend_catalogue()
        service = DatasetQA(engine, BareDialogue(remember_format, clarify_source), backend.gateway())
        try:
            sid, tid = begin(service.artifacts)
            first, second = [save(service.artifacts, sid, tid, value) for value in ["one", "two"]]
            publish(service.artifacts, sid, tid, [first, second])
            events = await collect(service, sid, "把其中一份记录保存为 CSV", "followup")
            assert events[-1]["status"] == "WAITING_INPUT"
            assert not backend.calls
            assert [item["handle"] for item in captured["items"]] == [first["file_artifact"], second["file_artifact"]]
        finally:
            await service.close()
    asyncio.run(run())


def test_explicit_older_result_routes_its_own_consumer_before_latest_delivery(engine, monkeypatch):
    async def run():
        backend = backend_catalogue()
        exporter = next(item for item in backend.catalog["tools"] if item.name == "materialize_records")
        backend.catalog["records-service"] = [deepcopy(exporter)]
        backend.catalog["other-service"] = [deepcopy(exporter)]
        prepared = {}
        original_prepare = ToolSession.prepare
        async def observe_prepare(tools, query, references=(), *, resources=()):
            prepared["resources"] = deepcopy(resources)
            await original_prepare(tools, query, references, resources=resources)
            prepared["loaded"] = [(tool.server, tool.name) for tool in tools.loaded.values()]
        monkeypatch.setattr(ToolSession, "prepare", observe_prepare)
        expected = {}
        def clarify_fields(messages, definitions):
            context = json.loads(messages[1].content)
            assert context["request_artifacts"]["items"][0]["handle"] == expected["old"]
            assert context["published_artifacts"]["items"][0]["handle"] == expected["new"]
            return action("request_input", missing="需要保留哪些字段", question="要保留哪些字段？")
        service = DatasetQA(engine, BareDialogue(clarify_fields), backend.gateway())
        try:
            sid, tid = begin(service.artifacts)
            older = save(service.artifacts, sid, tid, "older")
            publish(service.artifacts, sid, tid, [older])
            latest, _ = service.store.submit("alice", sid, "latest", {"message": "Find other records"}, None, service.owner)
            newer = {"result_id": latest["id"]+":0", "view_type": "table", "title": "Other records", "data": {"resource": {
                "source_ref": "another-reference", "format": "jsonl", "record_count": 2, "sha256": "b"*64}}}
            newer["file_artifact"] = service.artifacts.register("alice", sid, newer,
                SimpleNamespace(server="other-service", name="query"), ArtifactSpec())
            service.store.write("alice", sid, latest["id"], card=newer)
            publish(service.artifacts, sid, latest["id"], [newer])
            expected.update(old=older["file_artifact"], new=newer["file_artifact"])
            # Cache metadata without any business execution, as in an established session.
            async with service.gateway.session() as tools:
                for server in backend.catalog:
                    await tools.tools(server)
            events = await collect(service, sid, "save these records csv using selected fields", "followup",
                result_id=older["result_id"])
            assert events[-1]["status"] == "WAITING_INPUT"
            assert [item["server"] for item in prepared["resources"]] == ["records-service"]
            assert prepared["loaded"][1] == ("records-service", "materialize_records")
            assert not backend.calls
        finally:
            await service.close()
    asyncio.run(run())


@pytest.mark.parametrize("operation", ["filter", "export"])
def test_mixed_capability_checks_record_preservation_only_for_actual_export(engine, operation):
    async def run():
        backend = backend_catalogue()
        exporter = deepcopy(next(item for item in backend.catalog["tools"] if item.name == "materialize_records"))
        exporter.meta["piflow"]["qa"]["routing"]["operations"] = ["filter", "export"]
        tool = Tool("records-service", exporter.name, exporter.description, exporter.inputSchema,
            exporter.annotations, exporter.meta)
        service = DatasetQA(engine, BareDialogue(), backend.gateway())
        try:
            sid, tid = begin(service.artifacts)
            source = save(service.artifacts, sid, tid, "original")["data"]["resource"]
            execution = Execution()
            operation_id = execution.operations.register("Process records", {"server": tool.server, "name": tool.name})
            execution.operations.get(operation_id)["intent"] = {"operation": operation, "output_format": "csv"}
            execution.operations.start(operation_id, "call", {"server": tool.server, "name": tool.name})
            output = ToolResult({"resource": {"source_ref": "processed", "format": "csv",
                "record_count": 2, "sha256": "c"*64}, "parent_source_ref": source["source_ref"]})
            result_id = tid+":processed"
            async def persist():
                return await service._save_tool_result("alice", sid, tid, tool, output, operation_id,
                    "call", result_id, execution, {}, arguments={"source_ref": source["source_ref"], "format": "csv"})
            if operation == "export":
                with pytest.raises(QAError) as caught:
                    await persist()
                assert caught.value.code == "invalid_result"
                assert not service.store.results("alice", sid, result_id=result_id)
            else:
                card, created = await persist()
                assert created and card["data"]["resource"]["record_count"] == 2
                assert service.artifacts.get("alice", card["file_artifact"])["resource"]["record_count"] == 2
        finally:
            await service.close()
    asyncio.run(run())
