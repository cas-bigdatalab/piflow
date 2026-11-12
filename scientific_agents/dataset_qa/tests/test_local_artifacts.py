"""Persistent file delivery through the real MCP and mounted HTTP application."""
import asyncio
from concurrent.futures import ThreadPoolExecutor
import csv
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import time
from urllib.parse import urlsplit

from fastapi import FastAPI
from fastmcp import Client
import pytest
from starlette.testclient import TestClient

from mcp_servers.corpus_mcp import create_mcp_app, mcp
from services import corpus_connector_service as backend
from .. import artifact_storage as storage
from ..artifacts import execution_metadata
from ..contracts import QAError, Server
from ..capabilities import TASK
from ..mcp import MCPGateway, ToolSession
from ..responses import notice
from ..service import DatasetQA
from .test_dataset_qa import action, collect, engine, session
from .test_decisions import BareDialogue, payload, text
from .test_file_pipeline import SECRET, files, query_args, run_export, run_query
from .test_planning import approve


BASE = "https://testserver/api/piflow/v1/mcp"


@pytest.fixture
def download_client():
    mcp_app = create_mcp_app()
    app = FastAPI(lifespan=mcp_app.lifespan)
    app.mount("/api/piflow/v1/mcp", mcp_app)
    with TestClient(app, base_url="https://testserver") as client:
        yield client


def test_local_query_export_download_and_replay(files, download_client):
    original = run_query()
    exported = run_export(original["resource"])
    response = download_client.get(exported["downloadUrl"])
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "attachment" in response.headers["content-disposition"]
    assert response.headers["cache-control"] == "private, no-store"
    rows = list(csv.DictReader(io.StringIO(response.text)))
    assert [row["CID"] for row in rows] == ["1", "2"]
    assert hashlib.sha256(response.content).hexdigest() == exported["resource"]["sha256"]
    assert exported["statistics"] == original["statistics"]
    assert exported["parent_source_ref"] == original["resource"]["source_ref"]
    assert exported["record_count"] == 2
    assert run_query()["resource"]["source_ref"] == original["resource"]["source_ref"]
    assert run_export(original["resource"])["resource"]["source_ref"] == exported["resource"]["source_ref"]
    assert len(files.requests) == 2 and len(files.writes) == 4
    root = storage.persistent_root()
    assert len(list(root.glob("*/*/manifest.json"))) == 2
    assert not list(root.rglob(".pending-*"))
    assert set(original["resource"]) == {"source_ref", "name", "format", "fields", "record_count",
                                        "size_bytes", "sha256", "downloadUrl"}


def test_numeric_types_survive_local_csv_roundtrip(files):
    original = run_query(query_args(filters=None))
    csv_file = run_export(original["resource"])
    restored = run_export(csv_file["resource"], format="jsonl")
    assert restored["resource"]["sha256"] == original["resource"]["sha256"]
    assert len(files.requests) == 2


def test_concurrent_replay_commits_one_result(files):
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: run_query(), range(2)))
    assert results[0]["resource"]["source_ref"] == results[1]["resource"]["source_ref"]
    assert len(files.requests) == 2
    with ThreadPoolExecutor(max_workers=2) as pool:
        exports = list(pool.map(lambda _: run_export(results[0]["resource"]), range(2)))
    assert exports[0]["resource"]["source_ref"] == exports[1]["resource"]["source_ref"]
    assert len(list(storage.persistent_root().glob("*/*/manifest.json"))) == 2


def test_empty_result_is_persisted_and_not_requeried(files, monkeypatch):
    calls = []
    def empty(*args):
        calls.append(1)
        return {"IdentifierList": {"CID": []}}
    monkeypatch.setattr(backend, "_pubchem_request", empty)
    assert run_query()["resource"] is None
    assert run_query()["status"] == "empty"
    assert calls == [1]


def test_download_expiry_refresh_and_resource_are_independent(files, download_client, monkeypatch):
    result = run_query()
    old_link = result["downloadUrl"]
    future = time.time()+4000
    with monkeypatch.context() as patch:
        patch.setattr(storage.time, "time", lambda: future)
        assert download_client.get(old_link).status_code == 403
        refreshed = run_query()
        assert refreshed["resource"]["source_ref"] == result["resource"]["source_ref"]
        assert refreshed["downloadUrl"] != old_link
        assert download_client.get(refreshed["downloadUrl"]).status_code == 200
    assert len(files.requests) == 2


def test_download_rejects_tampering_names_and_resource_tokens(files, download_client):
    result = run_query()
    url = result["downloadUrl"]
    token, name = urlsplit(url).path.split("/")[-2:]
    bad_token = token[:-1]+("0" if token[-1] != "0" else "1")
    assert download_client.get(url.replace(token, bad_token)).status_code == 403
    assert download_client.get(url.replace(name, "someone-else.csv")).status_code == 403
    assert download_client.get(url.replace(token, result["resource"]["source_ref"])).status_code == 403
    with pytest.raises(ValueError):
        run_export(result["resource"], user="another-user")


def test_even_signed_path_traversal_is_rejected(files, download_client):
    token = storage.sign_token(SECRET, "qa-download-v1", {
        "owner": hashlib.sha256(b"user_a").hexdigest(), "key": "../private", "expires": int(time.time())+60})
    assert download_client.get(BASE+"/artifacts/"+token+"/file.jsonl").status_code == 403


def test_corrupted_file_is_neither_downloaded_nor_exported(files, download_client):
    result = run_query()
    path = next(storage.persistent_root().glob("*/*/data.jsonl"))
    path.write_bytes(path.read_bytes().replace(b"100.0", b"999.0"))
    response = download_client.get(result["downloadUrl"])
    assert response.status_code == 503 and "999" not in response.text
    with pytest.raises(storage.ArtifactStorageError):
        run_export(result["resource"])
    assert len(files.requests) == 2


def test_uncommitted_files_are_not_downloadable(files, download_client, monkeypatch):
    replace = storage.os.replace
    def interrupted(source, destination):
        if Path(destination).name == "manifest.json":
            raise OSError("private disk diagnostic")
        return replace(source, destination)
    monkeypatch.setattr(storage.os, "replace", interrupted)
    with pytest.raises(storage.ArtifactStorageError):
        run_query()
    root = storage.persistent_root()
    assert not list(root.glob("*/*/manifest.json")) and not list(root.rglob(".pending-*"))
    path = next(root.glob("*/*/data.jsonl"))
    token = storage.sign_token(SECRET, "qa-download-v1", {
        "owner": path.parent.parent.name, "key": path.parent.name, "expires": int(time.time())+60})
    assert download_client.get(BASE+"/artifacts/"+token+"/pubchem-compounds.jsonl").status_code == 404


@pytest.mark.parametrize("setting,value", [
    ("DATASET_QA_ARTIFACT_SIGNING_KEY", ""),
    ("DATASET_QA_ARTIFACT_BASE_URL", ""),
    ("DATASET_QA_ARTIFACT_BASE_URL", "https://secret:password@host/mcp"),
])
def test_invalid_config_is_reported_without_search_or_backend_details(files, monkeypatch, setting, value):
    monkeypatch.setenv(setting, value)
    async def run():
        async with MCPGateway({"files": Server(mcp)}).session() as tools:
            await tools.load("files", group="pubchem")
            tool = next(iter(tools.loaded.values()))
            with pytest.raises(QAError) as raised:
                await tools.call(tool.alias, query_args(),
                    metadata=execution_metadata("user_a", "request", query_args(), 120, secret=SECRET))
            assert raised.value.code == "artifact_unavailable"
            reply = notice(raised.value)
            assert "文件" in reply and "下载" in reply
            assert "没有匹配" not in reply and "其他数据集" not in reply
            assert "DATASET_QA" not in reply and "password" not in reply
        async with Client(mcp) as client:
            assert len(await client.list_tools()) == 8
    asyncio.run(run())
    assert not files.requests


def test_files_survive_reloaded_storage_configuration(files, download_client):
    result = run_query()
    # There is no process-local artifact map: fresh store instances resolve the
    # persisted manifest using only the stable signing key and resource handle.
    config = storage.StorageConfig.load()
    owner = hashlib.sha256(b"user_a").hexdigest()
    body = storage.verify_token(config.secret, "qa-resource-v2", result["resource"]["source_ref"][3:])
    reconstructed = storage.LocalArtifactStore(storage.StorageConfig.load(), owner)
    assert reconstructed.read_json(body["key"])["resource"]["source_ref"] == result["resource"]["source_ref"]
    assert download_client.get(result["downloadUrl"]).status_code == 200
    assert run_export(result["resource"])["record_count"] == 2
    assert len(files.requests) == 2


def test_new_process_exports_persisted_resource_without_requery(files):
    result = run_query()
    script = '''
import json, sys
from services import corpus_connector_service as backend
from scientific_agents.dataset_qa.artifacts import execution_metadata
def forbidden(*args):
    raise AssertionError("No source query is needed")
backend._pubchem_request = forbidden
resource = json.load(sys.stdin)
args = {"source_ref": resource["source_ref"], "format": "csv"}
meta = execution_metadata("user_a", "new-process-export", args, 60)["piflow_execution"]
result = backend.export_record_file(**args, execution=meta)
print(json.dumps({"count": result["record_count"], "parent": result["parent_source_ref"]}))
'''
    child = subprocess.run([sys.executable, "-c", script], input=json.dumps(result["resource"]),
        text=True, capture_output=True, timeout=30, check=True)
    assert json.loads(child.stdout) == {"count": 2, "parent": result["resource"]["source_ref"]}


@pytest.mark.parametrize("resource", ["invalid", {"name": "pubchem-compounds.jsonl", "format": "jsonl"}])
def test_invalid_committed_metadata_has_safe_download_feedback(files, download_client, resource):
    result = run_query()
    manifest = next(storage.persistent_root().glob("*/*/manifest.json"))
    manifest.write_text(json.dumps({"resource": resource}), encoding="utf-8")
    response = download_client.get(result["downloadUrl"])
    assert response.status_code == 503 and response.json()["message"]
    with pytest.raises(storage.ArtifactStorageError):
        run_query()
    assert len(files.requests) == 2


@pytest.mark.parametrize("version,backend_name", [("v1", None), ("v2", "minio"), ("v2", "unknown"), ("v3", "local")])
def test_unsupported_resource_cannot_be_reinterpreted_as_local(files, version, backend_name):
    result = run_query()
    resource = result["resource"]
    body = storage.verify_token(SECRET, "qa-resource-v2", resource["source_ref"][3:])
    if backend_name is None:
        body.pop("backend")
    else:
        body["backend"] = backend_name
    foreign = version+"."+storage.sign_token(SECRET, "qa-resource-"+version, body)
    writes = list(files.writes)
    with pytest.raises(ValueError):
        run_export({**resource, "source_ref": foreign})
    assert files.writes == writes and len(files.requests) == 2


def test_disk_capacity_check_prevents_publication(files, monkeypatch):
    from types import SimpleNamespace
    monkeypatch.setattr(storage.shutil, "disk_usage", lambda _: SimpleNamespace(free=0))
    with pytest.raises(storage.ArtifactStorageError):
        run_query()
    assert not list(storage.persistent_root().glob("*/*/manifest.json"))


def test_symlink_cannot_redirect_an_owners_artifact(files, tmp_path):
    root = storage.persistent_root()
    root.mkdir(exist_ok=True)
    outside = tmp_path / "outside"
    outside.mkdir()
    owner = hashlib.sha256(b"user_a").hexdigest()
    try:
        (root / owner).symlink_to(outside, target_is_directory=True)
    except OSError:
        if sys.platform != "win32":
            raise
        # Directory junctions exercise the same escape guard on Windows
        # without requiring the symbolic-link privilege.
        import _winapi
        _winapi.CreateJunction(str(outside), str(root / owner))
    store = storage.LocalArtifactStore(storage.StorageConfig.load(), owner)
    with pytest.raises(storage.ArtifactStorageError):
        store.read_json("0"*64)


def test_default_root_is_outside_host_public_download_trees(monkeypatch):
    from infra.config_loader import PROJECT_ROOT
    from runtime.workspace_manager import WorkspaceManager
    monkeypatch.delenv("DATASET_QA_ARTIFACT_ROOT", raising=False)
    root = storage.persistent_root()
    workspace = WorkspaceManager().root.resolve()
    assert not root.is_relative_to(workspace)
    assert not root.is_relative_to((PROJECT_ROOT / "storage").resolve())
    for public in (workspace / "artifacts" / "qa", PROJECT_ROOT / "storage" / "qa"):
        monkeypatch.setenv("DATASET_QA_ARTIFACT_ROOT", str(public))
        with pytest.raises(storage.ArtifactStorageError):
            storage.persistent_root()


@pytest.mark.parametrize("phase", ["prepare", "publish"])
def test_qa_storage_problem_has_friendly_feedback_without_repeating_search(engine, files, monkeypatch, phase):
    if phase == "prepare":
        monkeypatch.setenv("DATASET_QA_ARTIFACT_BASE_URL", "")
    else:
        def unavailable(*args):
            raise storage.ArtifactStorageError("PRIVATE_STORAGE_DIAGNOSTIC")
        monkeypatch.setattr(storage.LocalArtifactStore, "put_json", unavailable)
    def query(messages, definitions):
        name = next(d["function"]["name"] for d in definitions if d["function"]["name"].endswith("_query_pubchem_compounds"))
        return action(name, **query_args(), **{TASK: {"complete_request": True}})
    async def run():
        service = DatasetQA(engine, BareDialogue(query, query, text()), MCPGateway({"piflow-corpus": Server(mcp)}))
        sid = session(service)
        try:
            events = await collect(service, sid, "PubChem 查找相似化合物 SMILES CC")
            saved = payload(service, sid, events)
            assert saved["error"]["error_code"] == "artifact_unavailable"
            reply = "".join(event.get("text", "") for event in events if event["type"] == "message")
            assert "结果文件尚未准备好" in reply
            assert not any(value in reply for value in ("PRIVATE_STORAGE", "执行失败", "没有匹配", "选择其他数据集"))
        finally:
            await service.close()
    asyncio.run(run())
    assert len(files.requests) == (0 if phase == "prepare" else 2)


def file_plan():
    return {"outcomes": [{"key": "file", "description": "符合条件的 CSV 文件", "kind": "exported_file"}],
        "steps": [{"key": "query", "tool": "query_pubchem_compounds", "arguments": query_args()},
            {"key": "export", "tool": "export_dataset", "object": {"step": "query", "path": "/resource"},
                "arguments": {"format": "csv"}, "produces": ["file"]}]}


@pytest.mark.parametrize("mode", ["direct", "react", "plan"])
@pytest.mark.parametrize("fault", ["key", "url", "permission", "space", "publish"])
def test_storage_failures_close_all_entry_paths(engine, files, monkeypatch, mode, fault):
    if fault == "key":
        monkeypatch.delenv("DATASET_QA_ARTIFACT_SIGNING_KEY", raising=False)
    elif fault == "url":
        monkeypatch.setenv("DATASET_QA_ARTIFACT_BASE_URL", "")
    elif fault == "permission":
        def denied(*args, **kwargs):
            raise PermissionError("PRIVATE_DISK_PERMISSION")
        monkeypatch.setattr(storage.tempfile, "TemporaryFile", denied)
    elif fault == "space":
        from types import SimpleNamespace
        monkeypatch.setattr(storage.shutil, "disk_usage", lambda _: SimpleNamespace(free=0))
    else:
        def denied(*args, **kwargs):
            raise storage.ArtifactStorageError("PRIVATE_DISK_FULL", phase="publish")
        monkeypatch.setattr(storage.LocalArtifactStore, "put_json", denied)
    calls = []
    original = ToolSession.call
    async def count(self, alias, arguments, **kwargs):
        calls.append(alias)
        return await original(self, alias, arguments, **kwargs)
    monkeypatch.setattr(ToolSession, "call", count)
    def query(messages, definitions):
        alias = next(d["function"]["name"] for d in definitions if d["function"]["name"].endswith("_query_pubchem_compounds"))
        return action(alias, **query_args(), **({TASK: {"complete_request": True}} if mode == "direct" else {}))
    steps = ([action("remember", plan=file_plan()), approve] if mode == "plan" else
        [query, action("remember", invalid_field=True)] if mode == "react" else [query])
    async def run():
        dialogue = BareDialogue(action("load_mcp_tools", server="piflow-corpus"), *steps)
        service = DatasetQA(engine, dialogue, MCPGateway({"piflow-corpus": Server(mcp)}))
        try:
            sid = session(service)
            events = await collect(service, sid, "按给定结构和数值条件检索，并导出 CSV")
            saved = payload(service, sid, events)
            assert saved["error"]["error_code"] == "artifact_unavailable"
            assert len(dialogue.inputs) == (2 if mode == "direct" else 3)
            assert len(calls) == int(fault != "key")
            assert len(files.requests) == (2 if fault == "publish" else 0)
            attempt = saved["operations"][0]["attempts"][0]
            assert attempt.get("dispatched", True) is (fault != "key")
            assert attempt["error"]["detail"]["phase"] == {
                "key": "execution_context", "url": "configuration", "permission": "prepare", "space": "prepare", "publish": "publish"}[fault]
            reply = "".join(e.get("text", "") for e in events if e["type"] == "message")
            assert "文件尚未准备好" in reply
            assert not any(word in reply for word in ("PRIVATE_", "DATASET_QA", "确认操作对象", "参数", "。。"))
            assert "按给定结构和数值条件检索，并导出 CSV" not in reply
        finally:
            await service.close()
    asyncio.run(run())


def test_restored_configuration_allows_next_turn_without_recreating_session(engine, files, monkeypatch):
    monkeypatch.delenv("DATASET_QA_ARTIFACT_SIGNING_KEY", raising=False)
    async def run():
        dialogue = BareDialogue(action("load_mcp_tools", server="piflow-corpus"),
            action("remember", plan=file_plan()), approve)
        service = DatasetQA(engine, dialogue, MCPGateway({"piflow-corpus": Server(mcp)}))
        try:
            sid = session(service)
            first = await collect(service, sid, "检索并生成 CSV")
            assert payload(service, sid, first)["error"]["error_code"] == "artifact_unavailable"
            monkeypatch.setenv("DATASET_QA_ARTIFACT_SIGNING_KEY", SECRET)
            service.dialogue = BareDialogue(action("remember", plan=file_plan()), approve, text())
            second = await collect(service, sid, "按原来的条件重新检索并生成 CSV", rid="recovered")
            assert payload(service, sid, second).get("error") is None
            assert len(files.requests) == 2
            assert len(service.artifacts.recent("alice")) == 2
        finally:
            await service.close()
    asyncio.run(run())


def test_export_failure_preserves_source_for_reuse_without_querying_again(engine, files, monkeypatch):
    original = storage.LocalArtifactStore.put_file
    def deny_csv(store, key, path, fmt):
        if fmt == "csv":
            raise storage.ArtifactStorageError("PRIVATE_EXPORT", phase="publish")
        return original(store, key, path, fmt)
    monkeypatch.setattr(storage.LocalArtifactStore, "put_file", deny_csv)
    async def run():
        dialogue = BareDialogue(action("load_mcp_tools", server="piflow-corpus"),
            action("remember", plan=file_plan()), approve)
        service = DatasetQA(engine, dialogue, MCPGateway({"piflow-corpus": Server(mcp)}))
        try:
            sid = session(service)
            events = await collect(service, sid, "检索后导出 CSV")
            assert payload(service, sid, events)["error"]["error_code"] == "artifact_unavailable"
            assert len(dialogue.inputs) == 3 and len(files.requests) == 2
            artifacts = service.artifacts.recent("alice")
            assert len(artifacts) == 1
            source = service.artifacts.get("alice", artifacts[0]["handle"])["resource"]
            monkeypatch.setattr(storage.LocalArtifactStore, "put_file", original)
            result = run_export(source, user="alice")
            assert result["resource"]["format"] == "csv" and result["record_count"] == 2
            assert len(files.requests) == 2
        finally:
            await service.close()
    asyncio.run(run())
