from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

from piflow_engine.cn.piflow.core.flow import FlowImpl
from piflow_engine.cn.piflow.core.process_impl import ProcessImpl
from piflow_engine.cn.piflow.core.runner import Runner
from piflow_engine.cn.piflow.core.stop_job import StopJobImpl


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "engine"
    / "local"
    / "corpus_dataset_source_stop.py"
)
MODULE_NAME = "piflow_engine.cn.piflow.engine.local.corpus_dataset_source_stop_test"
_SPEC = importlib.util.spec_from_file_location(MODULE_NAME, MODULE_PATH)
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError(f"failed to load module spec from {MODULE_PATH}")
corpus_source_module = importlib.util.module_from_spec(_SPEC)
sys.modules[MODULE_NAME] = corpus_source_module
_SPEC.loader.exec_module(corpus_source_module)
CorpusDatasetSourceStop = corpus_source_module.CorpusDatasetSourceStop
RUNNER_CONTEXT_WORKSPACE_ROOT = "local.workspace_root"


class _FakeResponse:
    def __init__(self, *, text: str = "", chunks: list[bytes] | None = None) -> None:
        self.text = text
        self._chunks = chunks or []
        payload = b"".join(self._chunks) if self._chunks else self.text.encode("utf-8")
        self._buffer = payload

    def iter_content(self, chunk_size: int = 1024):
        del chunk_size
        yield from self._chunks

    def read(self, size: int = -1):
        if size is None or size < 0:
            size = len(self._buffer)
        chunk = self._buffer[:size]
        self._buffer = self._buffer[size:]
        return chunk

    def __enter__(self) -> "_FakeResponse":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None


def test_corpus_dataset_source_stop_outputs_first_file_as_output_by_default(tmp_path: Path, monkeypatch) -> None:
    workspace_root = tmp_path / "workspace"
    dataset_detail_json = (
        '{"code":200,"message":"OK","data":{"connectorId":"DS-NODE-1","cstr":"ES-CORPUS-B138",'
        '"fromName":"连接器节点1","id":"6a744595d38ea034d388c7b4","size":"0.01","title":"1900年以来中国地震目录语料"},'
        '"timestamp":1787104759250}'
    )
    download_urls_json = (
        '{"code":200,"message":"OK","data":['
        '{"fileName":"es-corpus-b138.tar","downloadUrl":null,'
        '"url":"http://10.0.82.213:7004/dataset.file.download/ES-CORPUS-B138/es-corpus-b138.tar"},'
        '{"fileName":"es-corpus-b138-extra.tar",'
        '"url":"http://10.0.82.213:7004/dataset.file.download/ES-CORPUS-B138/es-corpus-b138-extra.tar"}'
        '],"timestamp":1787121515520}'
    )

    def fake_urlopen(url: str, *args, **kwargs):
        del args, kwargs
        if url.endswith("/dataset.queryDataset?id=6a744595d38ea034d388c7b4"):
            return _FakeResponse(text=dataset_detail_json)
        if url.endswith("/dataset.files?cstr=ES-CORPUS-B138"):
            return _FakeResponse(text=download_urls_json)
        if url.endswith("/es-corpus-b138.tar"):
            return _FakeResponse(chunks=[b"primary tar"])
        if url.endswith("/es-corpus-b138-extra.tar"):
            return _FakeResponse(chunks=[b"extra tar"])
        raise AssertionError(f"unexpected url: {url}")

    monkeypatch.setattr(corpus_source_module, "urlopen", fake_urlopen)
    monkeypatch.setattr(
        corpus_source_module,
        "_get_settings",
        lambda: type("Settings", (), {"corpus_route": type("CorpusRoute", (), {"base_url": "http://10.0.82.213:7003/"})()})(),
    )

    stop = CorpusDatasetSourceStop()
    stop.set_properties({"dataset_id": "6a744595d38ea034d388c7b4"})

    runner = Runner.create().bind(RUNNER_CONTEXT_WORKSPACE_ROOT, str(workspace_root))
    flow = FlowImpl(name="test", uuid="flow-1")
    process = ProcessImpl(flow, runner.context, runner)
    process_context = process._process_context

    stop.initialize(process_context)
    stop_job = StopJobImpl("CorpusDatasetSource", stop, process_context)
    outputs = stop_job.perform({})

    primary = outputs.get_artifact("output")

    assert Path(primary.path).exists()
    assert Path(primary.path).read_bytes() == b"primary tar"
    assert primary.metadata["datasetId"] == "6a744595d38ea034d388c7b4"
    assert primary.metadata["cstr"] == "ES-CORPUS-B138"
    assert primary.metadata["connectorId"] == "DS-NODE-1"
    assert primary.metadata["fileName"] == "es-corpus-b138.tar"
    assert primary.metadata["size"] == "0.01"
    assert primary.metadata["fromName"] == "连接器节点1"


def test_corpus_dataset_source_stop_outputs_requested_file_name(tmp_path: Path, monkeypatch) -> None:
    workspace_root = tmp_path / "workspace"
    dataset_detail_json = (
        '{"code":200,"message":"OK","data":{"connectorId":"DS-NODE-1","cstr":"ES-CORPUS-B138",'
        '"fromName":"连接器节点1","id":"6a744595d38ea034d388c7b4","size":"0.01","title":"1900年以来中国地震目录语料"},'
        '"timestamp":1787104759250}'
    )
    download_urls_json = (
        '{"code":200,"message":"OK","data":['
        '{"downloadUrls":['
        '"http://10.0.82.213:7004/corpus.dataset.file.download/ES-CORPUS-B138/es-corpus-b138.tar",'
        '"http://10.0.82.213:7004/corpus.dataset.file.download/ES-CORPUS-B138/es-corpus-b138-extra.tar"'
        '],"name":"连接器节点1"}'
        '],"timestamp":1787121515520}'
    )

    def fake_urlopen(url: str, *args, **kwargs):
        del args, kwargs
        if url.endswith("/dataset.queryDataset?id=6a744595d38ea034d388c7b4"):
            return _FakeResponse(text=dataset_detail_json)
        if url.endswith("/dataset.files?cstr=ES-CORPUS-B138"):
            return _FakeResponse(text=download_urls_json)
        if url.endswith("/es-corpus-b138.tar"):
            return _FakeResponse(chunks=[b"primary tar"])
        if url.endswith("/es-corpus-b138-extra.tar"):
            return _FakeResponse(chunks=[b"extra tar"])
        raise AssertionError(f"unexpected url: {url}")

    monkeypatch.setattr(corpus_source_module, "urlopen", fake_urlopen)
    monkeypatch.setattr(
        corpus_source_module,
        "_get_settings",
        lambda: type("Settings", (), {"corpus_route": type("CorpusRoute", (), {"base_url": "http://10.0.82.213:7003/"})()})(),
    )

    stop = CorpusDatasetSourceStop()
    stop.set_properties({"dataset_id": "6a744595d38ea034d388c7b4", "fileName": "es-corpus-b138-extra.tar"})

    runner = Runner.create().bind(RUNNER_CONTEXT_WORKSPACE_ROOT, str(workspace_root))
    flow = FlowImpl(name="test", uuid="flow-1")
    process = ProcessImpl(flow, runner.context, runner)
    process_context = process._process_context

    stop.initialize(process_context)
    stop_job = StopJobImpl("CorpusDatasetSource", stop, process_context)
    outputs = stop_job.perform({})

    artifact = outputs.get_artifact("output")

    assert Path(artifact.path).exists()
    assert Path(artifact.path).read_bytes() == b"extra tar"
    assert artifact.metadata["fileName"] == "es-corpus-b138-extra.tar"


def test_corpus_dataset_source_stop_uses_first_record_when_file_name_is_duplicated() -> None:
    stop = CorpusDatasetSourceStop()
    stop.set_properties({"dataset_id": "6a6ab4da15840cf004056867"})

    first = {
        "fileName": "es-corpus-k024.tar",
        "downloadUrl": "http://10.0.82.213:7004/first/es-corpus-k024.tar",
    }
    second = {
        "fileName": "es-corpus-k024.tar",
        "downloadUrl": "http://10.0.82.214:7004/second/es-corpus-k024.tar",
    }

    assert stop._select_record([first, second]) is first


@pytest.mark.parametrize("data,error", [(None, "detail is empty"), ({}, "detail is empty"), ([], "must be an object")])
def test_empty_or_invalid_detail_is_reported_before_cstr_lookup(monkeypatch, data, error):
    stop = CorpusDatasetSourceStop()
    stop._base_url = "http://corpus.example"
    monkeypatch.setattr(corpus_source_module, "urlopen", lambda *a, **kw: _FakeResponse(
        text=json.dumps({"code": 200, "data": data})))
    with pytest.raises(ValueError, match=error):
        stop._fetch_dataset_detail("dataset-id")


@pytest.mark.parametrize("cstr", [None, "", "  "])
def test_missing_cstr_is_not_used_as_download_identifier(tmp_path, monkeypatch, cstr):
    stop = CorpusDatasetSourceStop()
    stop._base_url = "http://corpus.example"
    stop._workspace_root = tmp_path
    stop.dataset_id = "dataset-id"
    monkeypatch.setattr(stop, "_fetch_dataset_detail", lambda _: {"id": "dataset-id", "cstr": cstr})
    with pytest.raises(ValueError, match="does not contain cstr"):
        stop.perform(None, None, None)


def test_file_list_builds_encoded_download_url_when_only_filename_is_available(monkeypatch):
    stop = CorpusDatasetSourceStop()
    stop._base_url = "http://corpus.example"
    def open_files(url, **kwargs):
        assert url == "http://corpus.example/dataset.files?cstr=CODE%2FA"
        return _FakeResponse(text=json.dumps({"code": 200, "data": [{"fileName": "a b.tar"}]}))
    monkeypatch.setattr(corpus_source_module, "urlopen", open_files)
    records = stop._fetch_download_urls("CODE/A", dataset={})
    assert records == [{"fileName": "a b.tar", "downloadUrl": "http://corpus.example/dataset.file.download/CODE%2FA/a%20b.tar", "dataset": {}}]


def test_empty_file_list_stays_empty(monkeypatch):
    stop = CorpusDatasetSourceStop()
    stop._base_url = "http://corpus.example"
    monkeypatch.setattr(corpus_source_module, "urlopen", lambda *a, **kw: _FakeResponse(text='{"code":200,"data":[]}'))
    assert stop._fetch_download_urls("CODE", dataset={}) == []
