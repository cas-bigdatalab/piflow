"""Real MCP and QA scheduling with deterministic upstream and object storage."""
import asyncio
from copy import deepcopy
import csv
import io
import json
from pathlib import Path
from types import SimpleNamespace
import time

from fastmcp import Client
from minio.error import S3Error
import pytest

from services import corpus_connector_service as backend
from mcp_servers.corpus_mcp import mcp
from ..artifacts import execution_metadata
from ..contracts import Server
from ..execution import Execution
from ..mcp import MCPGateway, Tool
from ..plan_runtime import install_plan
from ..planning import Check, Plan
from ..service import DatasetQA
from .test_dataset_qa import action, collect, engine, result_cards, session
from .test_decisions import BareDialogue, payload, text
from .test_planning import approve


SECRET = "test-only-file-execution-key"


class ObjectResponse(io.BytesIO):
    def release_conn(self):
        pass


class Objects:
    def __init__(self):
        self.data, self.writes = {}, []

    def get_object(self, bucket, key):
        if (bucket, key) not in self.data:
            raise S3Error(response=None, code="NoSuchKey", message="missing", resource=key, request_id="", host_id="")
        return ObjectResponse(self.data[bucket, key])

    def put_object(self, bucket, key, data, length, **kwargs):
        raw = data.read()
        assert len(raw) == length
        self.data[bucket, key] = raw
        self.writes.append(key)

    def fput_object(self, bucket, key, path, **kwargs):
        self.data[bucket, key] = Path(path).read_bytes()
        self.writes.append(key)

    def stat_object(self, bucket, key):
        return SimpleNamespace(size=len(self.data[bucket, key]))

    def presigned_get_object(self, bucket, key, **kwargs):
        return "https://storage.invalid/"+bucket+"/"+key+"?signature=test"


@pytest.fixture
def files(monkeypatch, tmp_path):
    objects = Objects()
    config = SimpleNamespace(secret_key=SECRET, base_prefix="results")
    monkeypatch.setattr(backend, "_result_storage", lambda: SimpleNamespace(
        client=objects, config=config, workspace=SimpleNamespace(temp=tmp_path)))
    from .. import service as service_module
    original = execution_metadata
    monkeypatch.setattr(service_module, "execution_metadata", lambda *args: original(*args, secret=SECRET))
    requests = []
    rows = [
        {"CID": 1, "SMILES": "CC", "MolecularWeight": "100", "XLogP": -1},
        {"CID": 2, "SMILES": "CCC", "MolecularWeight": "500", "XLogP": 5},
        {"CID": 3, "SMILES": "CCCC", "MolecularWeight": "501", "XLogP": 6},
        {"CID": 4, "SMILES": "CCCCC", "MolecularWeight": "200"},
    ]
    def request(client, route, data, params, root, deadline):
        requests.append((route, data, params))
        if "fastsimilarity" in route:
            return {"IdentifierList": {"CID": [1, 2, 2, 3, 4]}}
        return {"PropertyTable": {"Properties": deepcopy(rows)}}
    monkeypatch.setattr(backend, "_pubchem_request", request)
    return SimpleNamespace(objects=objects, requests=requests, rows=rows)


def query_args(**kwargs):
    return {"smiles": "CC(=O)OC1=CC=CC=C1C(=O)O", "similarity_threshold": 80,
        "filters": [{"field": "MolecularWeight", "minimum": 100, "maximum": 500},
            {"field": "XLogP", "minimum": -1, "maximum": 5}], "limit": 1000, **kwargs}


def run_query(args=None, *, user="user_a", request="query-1"):
    args = args or query_args()
    meta = execution_metadata(user, request, args, 120, secret=SECRET)
    return backend.query_pubchem_records(**args, execution=meta["piflow_execution"])


def run_export(resource, *, user="user_a", format="csv"):
    args = {"source_ref": resource["source_ref"], "format": format}
    meta = execution_metadata(user, "export-1", args, 120, secret=SECRET)
    return backend.export_record_file(**args, execution=meta["piflow_execution"])


def test_filter_limits_counts_replay_and_csv_contents(files):
    value = run_query()
    assert value["status"] == "ready" and value["record_count"] == 2
    assert value["target_met"] is False and value["coverage"] == "complete"
    assert value["statistics"] == {"candidates": 4, "checked": 4, "accepted": 2, "excluded": 2,
        "duplicate_candidates": 1, "exclusion_reasons": {"outside_MolecularWeight": 1, "missing_XLogP": 1},
        "reason_policy": "first_failed_condition"}
    assert run_query()["resource"]["source_ref"] == value["resource"]["source_ref"]
    assert len(files.requests) == 2
    exported = run_export(value["resource"])
    assert exported["record_count"] == 2 and exported["target_met"] is False
    bodies = [body for (_, key), body in files.objects.data.items() if key.endswith(".csv")]
    records = list(csv.DictReader(io.StringIO(bodies[0].decode())))
    assert [row["CID"] for row in records] == ["1", "2"]
    writes = len(files.objects.writes)
    assert run_export(value["resource"])["resource"]["sha256"] == exported["resource"]["sha256"]
    assert len(files.objects.writes) == writes and len(files.requests) == 2


@pytest.mark.parametrize("mutation", ["identity", "arguments", "deadline", "missing", "number", "string", "boolean"])
def test_execution_identity_cannot_be_forged(files, mutation):
    args = query_args()
    if mutation == "boolean":
        args["filters"][0]["minimum"] = 1
    meta = execution_metadata("user_a", "request", args, 120, secret=SECRET)["piflow_execution"]
    if mutation == "identity":
        meta["user"] = "user_b"
    elif mutation == "arguments":
        args["limit"] = 1
    elif mutation == "deadline":
        meta["deadline"] = time.time()-1
    elif mutation in {"number", "string", "boolean"}:
        args["filters"][0]["minimum"] = {"number": 100.5, "string": "100", "boolean": True}[mutation]
    else:
        meta = {}
    with pytest.raises(ValueError):
        backend.query_pubchem_records(**args, execution=meta)
    assert not files.requests and not files.objects.writes


def test_cross_user_and_tampered_resource_rejected(files):
    resource = run_query()["resource"]
    with pytest.raises(ValueError):
        run_export(resource, user="user_b")
    with pytest.raises(ValueError):
        run_export({**resource, "source_ref": resource["source_ref"]+"0"})


def test_target_count_stops_after_filtering_not_candidate_fetch(files):
    value = run_query(query_args(limit=1))
    assert value["record_count"] == 1
    assert value["target_met"] and value["stop_reason"] == "target_reached"
    assert value["coverage"] == "partial" and value["statistics"]["checked"] == 1


def test_csv_roundtrip_keeps_original_numeric_and_null_types(files):
    original = run_query(query_args(filters=None))
    csv_file = run_export(original["resource"])
    json_file = run_export(csv_file["resource"], format="jsonl")
    assert json_file["resource"]["sha256"] == original["resource"]["sha256"]


def test_corrupted_file_is_not_exported_as_valid(files):
    resource = run_query()["resource"]
    key = next(key for key in files.objects.data if key[1].endswith("data.jsonl"))
    files.objects.data[key] = files.objects.data[key].replace(b'100.0', b'999.0')
    with pytest.raises(ValueError, match="版本"):
        run_export(resource)


def test_interrupted_property_batches_return_scoped_partial_result(files, monkeypatch):
    calls = []
    def request(client, route, data, params, root, deadline):
        calls.append(route)
        if "fastsimilarity" in route:
            return {"IdentifierList": {"CID": list(range(1, 402))}}
        if len(calls) == 3:
            raise TimeoutError()
        return {"PropertyTable": {"Properties": [{"CID": n, "SMILES": "CC", "MolecularWeight": 200, "XLogP": 1} for n in range(1, 201)]}}
    monkeypatch.setattr(backend, "_pubchem_request", request)
    result = run_query()
    assert result["record_count"] == 200 and result["status"] == "ready"
    assert result["coverage"] == "partial" and result["stop_reason"] == "source_interrupted"
    assert result["statistics"]["checked"] == 200 and len(calls) == 3


def test_candidate_cap_is_not_source_exhaustion(files, monkeypatch):
    monkeypatch.setattr(backend, "_CANDIDATE_LIMIT", 5)
    result = run_query(query_args(limit=None))
    assert result["stop_reason"] == "candidate_limit" and result["coverage"] == "partial"


def test_artifact_handle_reused_across_sessions_without_query(engine, files):
    from ..capabilities import TASK, OBJECT
    from ..contracts import QAError
    async def run():
        service = DatasetQA(engine, BareDialogue(), MCPGateway({"piflow-corpus": Server(mcp)}))
        try:
            sid = session(service)
            def query(messages, definitions):
                name = next(d["function"]["name"] for d in definitions if d["function"]["name"].endswith("_query_pubchem_compounds"))
                return action(name, **query_args(), **{TASK: {"complete_request": True}})
            service.dialogue = BareDialogue(query, text())
            await collect(service, sid, "PubChem 查找相似化合物 SMILES CC")
            owned = service.artifacts.recent("alice")
            assert len(owned) == 1
            with pytest.raises(QAError):
                service.artifacts.get("bob", owned[0]["handle"])
            def export(messages, definitions):
                assert json.loads(messages[1].content)["available_artifacts"][0]["handle"] == owned[0]["handle"]
                name = next(d["function"]["name"] for d in definitions if d["function"]["name"].endswith("_export_dataset"))
                return action(name, format="csv", **{OBJECT: owned[0]["handle"], TASK: {"complete_request": True}})
            service.dialogue = BareDialogue(export, text())
            sid2 = session(service, request="second-session")
            values = await collect(service, sid2, "把上次的文件导出CSV")
            assert result_cards(values)[0]["data"]["items"][0]["resource"]["format"] == "csv"
            assert len(files.requests) == 2
        finally:
            await service.close()
    asyncio.run(run())


@pytest.mark.parametrize("query,expected", [
    ("PubChem SMILES similarity_search", "query_pubchem_compounds"),
    ("从 PubChem 找相似化合物，SMILES CC，相似度80%，分子量100到500，LogP为-1到5，下载1000条保存CSV", "query_pubchem_compounds"),
    ("我想找化学化工相关的数据集", "search_corpus_datasets"),
    ("看几条这个文件的内容", "read_corpus_file_records"),
    ("把上次的文件导出CSV", "export_dataset"),
])
def test_tools_filtered_by_group_and_relevance_before_history(query, expected):
    async def run():
        async with MCPGateway({"piflow-corpus": Server(mcp)}).session() as tools:
            await tools.tools("piflow-corpus")
            selected = tools.prime(query, [{"server": "piflow-corpus", "name": "get_corpus_dataset_detail"}])
            assert selected["items"][0]["tool"] == expected
            assert [item["tool"] for item in (await tools.load("piflow-corpus", group="data_processing"))["items"]] == ["export_dataset"]
            assert not (await tools.load("piflow-corpus", group="missing"))["items"]
    asyncio.run(run())


def test_lost_mcp_response_replays_same_execution_without_requery(files):
    import httpx
    calls = []
    def factory(target, **kwargs):
        client = Client(target, **kwargs)
        invoke = client.call_tool
        async def call(name, arguments, **options):
            calls.append(deepcopy(options["meta"]))
            result = await invoke(name, arguments, **options)
            if len(calls) == 1:
                raise httpx.ReadError("response lost after execution")
            return result
        client.call_tool = call
        return client
    async def run():
        gateway = MCPGateway({"files": Server(mcp)}, client_factory=factory)
        async with gateway.session() as tools:
            await tools.load("files", group="pubchem")
            tool = next(iter(tools.loaded.values()))
            args = query_args()
            _, result = await tools.call(tool.alias, args,
                metadata=execution_metadata("user_a", "replay", args, 120, secret=SECRET))
            assert result.data["record_count"] == 2
            assert len(calls) == 2 and calls[0] == calls[1]
            assert len(files.requests) == 2
    asyncio.run(run())


def test_empty_query_replay_does_not_repeat_search(files, monkeypatch):
    calls = []
    def request(*args):
        calls.append(1)
        return {"IdentifierList": {"CID": []}}
    monkeypatch.setattr(backend, "_pubchem_request", request)
    assert run_query()["status"] == "empty"
    assert run_query()["status"] == "empty"
    assert len(calls) == 1


def test_concurrent_exports_share_one_verified_file(files):
    from concurrent.futures import ThreadPoolExecutor
    resource = run_query()["resource"]
    with ThreadPoolExecutor(max_workers=2) as pool:
        outputs = list(pool.map(lambda _: run_export(resource), range(2)))
    assert outputs[0]["resource"]["sha256"] == outputs[1]["resource"]["sha256"]
    assert len([name for name in files.objects.writes if name.endswith(".csv")]) == 1


@pytest.mark.parametrize("overrides", [{}, {"similarity_threshold": 80.0}, {"limit": 1000.0},
    {"filters": [{"field": "MolecularWeight", "minimum": 100.0, "maximum": 500.0},
        {"field": "XLogP", "minimum": -1.0, "maximum": 5.0}]}])
def test_real_mcp_schema_and_signed_context_round_trip(files, overrides):
    async def run():
        async with Client(mcp) as client:
            definitions = await client.list_tools()
            assert len(definitions) == 8
            tool = next(t for t in definitions if t.name == "query_pubchem_compounds")
            assert "ctx" not in tool.inputSchema["properties"]
            args = query_args(**overrides)
            result = await client.call_tool(tool.name, args,
                meta=execution_metadata("user_a", "native", args, 120, secret=SECRET))
            assert not result.is_error and result.structured_content["record_count"] == 2
            # Numerically equivalent retries use the same execution and file,
            # including nested range conditions. Stored record types stay intact.
            integers = query_args()
            repeated = await client.call_tool(tool.name, integers,
                meta=execution_metadata("user_a", "native", integers, 120, secret=SECRET))
            assert repeated.structured_content["resource"]["source_ref"] == result.structured_content["resource"]["source_ref"]
            assert len(files.requests) == 2
    asyncio.run(run())


@pytest.mark.parametrize("empty", [False, True])
@pytest.mark.parametrize("quantity_check,quantity", [("at_least", 1000), ("equals", 1000), ("at_most", 1000),
    ("equals", 1000.0), ("equals", 2.0), ("equals", 2.5)])
def test_full_qa_plan_two_calls_and_empty_dependency_closure(engine, files, monkeypatch, empty, quantity_check, quantity):
    if empty:
        monkeypatch.setattr(backend, "_pubchem_request", lambda *args: {"IdentifierList": {"CID": []}})
    plan = {"outcomes": [{"key": "file", "description": "符合条件的 CSV 文件", "kind": "exported_file",
        "checks": [{"path": "/record_count", "test": quantity_check, "value": quantity}]}],
        "steps": [{"key": "query", "tool": "query_pubchem_compounds", "arguments": query_args()},
            {"key": "export", "tool": "export_dataset", "object": {"step": "query", "path": "/resource"},
                "arguments": {"format": "csv"}, "produces": ["file"]}]}
    async def run():
        dialogue = BareDialogue(action("load_mcp_tools", server="piflow-corpus", query="PubChem CSV"),
            action("remember", plan=plan), approve, text())
        service = DatasetQA(engine, dialogue, MCPGateway({"piflow-corpus": Server(mcp)}))
        sid = session(service)
        try:
            values = await collect(service, sid, "从 PubChem 找相似度80%的化合物，分子量100到500，XLogP为-1到5，取1000条并导出CSV")
            saved = payload(service, sid, values)
            if empty:
                assert saved["operations"][1]["state"] == "unavailable"
            assert saved["plan"]["acceptance"]["file"]["state"] == ("unavailable" if empty else "accepted")
            outcome = saved["plan"]["spec"]["outcomes"][0]
            if quantity_check == "at_most":
                assert outcome["targets"] == []
                assert outcome["checks"] == [{"path": "/record_count", "test": "at_most", "value": 1000, "optional": False}]
            else:
                assert saved["plan"]["acceptance"]["file"]["targets_met"] is (not empty and quantity == 2)
                if quantity_check == "equals":
                    assert outcome["checks"] == [{"path": "/record_count", "test": "at_most", "value": quantity, "optional": False}]
                    assert outcome["targets"][0]["value"] == quantity
            assert len(dialogue.inputs) == 4
            if not empty:
                cards = result_cards(values)
                assert len(cards) == 1 and cards[0]["data"]["items"][0]["record_count"] == 2
                assert len(service.artifacts.recent("alice")) == 2
            else:
                assert saved["operations"][1]["state"] == "unavailable"
        finally:
            await service.close()
    asyncio.run(run())


@pytest.mark.parametrize("quantity", [1000, 1000.0, 2.5, "1000", True])
def test_quantity_normalization_keeps_upper_bound_and_non_numeric_identity(engine, quantity):
    async def run():
        tool = Tool("files", "read", "", {"type": "object", "properties": {}}, {},
            {"piflow": {"qa": {"result": {"kind": "records", "target_paths": ["/record_count"]}}}})
        tools = SimpleNamespace(loaded={tool.alias: tool}, validate=lambda *args: None)
        plan = Plan.model_validate({"outcomes": [{"key": "data", "description": "Records", "kind": "records",
            "checks": [{"path": path, "test": "equals", "value": quantity} for path in ("/record_count", "/identifier")]}],
            "steps": [{"key": "read", "tool": tool.alias, "produces": ["data"]}]})
        service = DatasetQA(engine, BareDialogue(), MCPGateway({}))
        saved = {}
        try:
            await install_plan(service, "alice", session(service), plan, tools, Execution(), saved, {})
            outcome = saved["plan"]["spec"]["outcomes"][0]
            assert outcome["checks"][1] == plan.outcomes[0].checks[1].model_dump()
            if type(quantity) in {int, float}:
                check = Check.model_validate(outcome["checks"][0])
                assert check.test == "at_most" and check.value == quantity
                assert check.matches({"record_count": 1}) and not check.matches({"record_count": quantity+1})
                assert outcome["targets"][0]["value"] == quantity
            else:
                assert outcome["checks"] == [item.model_dump() for item in plan.outcomes[0].checks]
                assert outcome["targets"] == []
        finally:
            await service.close()
    asyncio.run(run())
