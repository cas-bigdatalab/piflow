"""Source filtering applies upstream on every page, only to the XDC catalog."""
from types import SimpleNamespace
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlsplit

import pytest

from infra import config_loader
from infra.settings import CorpusRouteConfig
from runtime.cross_dag import corpus_registry


@pytest.fixture
def configure(monkeypatch):
    def apply(names):
        settings = SimpleNamespace(corpus_route=CorpusRouteConfig(
            base_url="http://corpus.example", cross_dag_dataset_filters={"source": names}))
        monkeypatch.setattr(config_loader, "get_settings", lambda: settings)
    return apply


@pytest.mark.parametrize("names", [[], ["", "  "]])
def test_empty_source_keeps_unfiltered_pagination(monkeypatch, configure, names):
    configure(names)
    calls = []

    def post(url, body):
        page = int(parse_qs(urlsplit(url).query)["pageNum"][0])
        calls.append((page, body))
        return {"data": {"content": [{"id": f"dataset-{page}"}], "totalPages": 2}}

    monkeypatch.setattr(corpus_registry, "_post_json", post)
    assert corpus_registry._fetch_datasets("http://corpus.example") == [{"id": "dataset-1"}, {"id": "dataset-2"}]
    assert calls == [(1, {}), (2, {})]
    assert CorpusRouteConfig().cross_dag_dataset_filters.source == []


def test_multiple_sources_use_one_array_on_every_page_and_deduplicate_results(monkeypatch, configure):
    configure([" Node A ", "Node B", "Node A", ""])
    calls = []

    def post(url, body):
        parts = urlsplit(url)
        query = parse_qs(parts.query)
        page = int(query["pageNum"][0])
        assert parts.path == "/dataset.page"
        assert query["pageSize"] == ["100"]
        assert "source" not in query and "sources" not in query
        assert body == {"sources": ["Node A", "Node B"]}
        calls.append(page)
        rows = [{"id": "shared"}] if page == 1 else [{"id": "shared"}, {"id": "Node A"}, {"id": "Node B"}]
        return {"data": {"content": rows, "totalPages": 2}}

    monkeypatch.setattr(corpus_registry, "_post_json", post)
    assert corpus_registry._fetch_datasets("http://corpus.example") == [
        {"id": "shared"}, {"id": "Node A"}, {"id": "Node B"}]
    assert calls == [1, 2]


@pytest.mark.parametrize("fails", [False, True])
def test_no_match_or_failure_never_retries_without_filter(monkeypatch, configure, fails):
    configure(["Node A"])
    calls = []

    def post(url, body):
        calls.append(body)
        if fails:
            raise HTTPError(url, 405, "Method Not Allowed", {}, None)
        return {"data": {"content": [], "totalPages": 0}}

    monkeypatch.setattr(corpus_registry, "_post_json", post)
    if fails:
        with pytest.raises(HTTPError):
            corpus_registry._fetch_datasets("http://corpus.example")
    else:
        assert corpus_registry._fetch_datasets("http://corpus.example") == []
    assert calls == [{"sources": ["Node A"]}]


def test_registered_catalog_refresh_preserves_filter_and_connector_request(monkeypatch, configure):
    configure(["Node A"])
    get_calls, post_calls = [], []

    def get(url):
        get_calls.append(url)
        return {"data": [{"connectorId": "node-a", "name": "Node A", "serviceUrl": "http://node-a:7003"}]}

    def post(url, body):
        post_calls.append(body)
        return {"data": [{"id": f"dataset-{len(post_calls)}", "name": "Sample dataset", "connectorId": "node-a"}]}

    monkeypatch.setattr(corpus_registry, "_get_json", get)
    monkeypatch.setattr(corpus_registry, "_post_json", post)
    registry = corpus_registry.build_corpus_registry(base_url="http://corpus.example", fetch_metrics=False, facet_fields=[])
    assert [d.dataset_id for d in registry.list_datasets()] == ["dataset-1"]
    assert [d.dataset_id for d in registry.list_datasets()] == ["dataset-1"]
    registry.refresh()
    assert [d.dataset_id for d in registry.list_datasets()] == ["dataset-2"]
    assert post_calls == [{"sources": ["Node A"]}] * 2
    assert get_calls == ["http://corpus.example/dataset.connector.page?pageNum=1&pageSize=100"] * 2


@pytest.fixture
def catalog(monkeypatch, configure):
    configure(["Node A", "Node B"])
    connectors = [
        {"connectorId": "node-a", "name": "Node A", "serviceUrl": "http://shared:7005"},
        {"connectorId": "node-b", "name": "Node B", "serviceUrl": "http://shared:7005"},
    ]
    datasets = [
        {"id": "dataset-a", "source": " Node A "},
        {"id": "dataset-b", "source": "Node B"},
    ]
    monkeypatch.setattr(corpus_registry, "_get_json", lambda url: {"data": connectors})
    monkeypatch.setattr(corpus_registry, "_post_json", lambda url, body: {"data": datasets})
    registry = corpus_registry.build_corpus_registry(
        base_url="http://corpus.example", fetch_metrics=False, facet_fields=[])
    return registry, connectors, datasets


def test_source_name_resolves_multiple_connectors_sharing_one_host(catalog):
    registry, connectors, raw_datasets = catalog
    connectors[0]["name"] = " Node A "
    datasets = registry.list_datasets()
    assert [d.dataset_id for d in datasets] == ["dataset-a", "dataset-b"]
    for dataset, connector in zip(datasets, connectors):
        assert connector["connectorId"] in dataset.tags
        assert dataset.replicas[0].source_ip == "shared"
        assert dataset.replicas[0].locator == dataset.dataset_id
        assert dataset.replicas[0].status == "AVAILABLE"
    assert all("connectorId" not in raw for raw in raw_datasets)


@pytest.mark.parametrize("source,count", [("Unknown", 0), ("Node", 0), ("Node A", 2)])
def test_source_name_requires_unique_exact_match(catalog, caplog, source, count):
    registry, connectors, datasets = catalog
    if count == 2:
        connectors[1]["name"] = "Node A"
    datasets[:] = [{"id": "dataset", "source": source}]
    assert registry.list_datasets() == []
    assert f"匹配到 {count} 个连接器" in caplog.text


def test_explicit_connector_references_take_precedence_over_source_name(catalog):
    registry, connectors, datasets = catalog
    connectors[0]["serviceUrl"] = "http://host-a:7005"
    datasets[:] = [{"id": "dataset", "source": "Unknown", "connectorId": ["node-a", "node-b"]}]
    dataset = registry.list_datasets()[0]
    assert [r.source_ip for r in dataset.replicas] == ["host-a", "shared"]
    assert [r.replica_id for r in dataset.replicas] == ["dataset@node-a", "dataset@node-b"]


def test_source_name_index_is_rebuilt_on_refresh(catalog, caplog):
    registry, connectors, datasets = catalog
    assert len(registry.list_datasets()) == 2
    connectors[:] = [{"connectorId": "new-a", "name": "Node A", "serviceUrl": "http://new-host:7005"}]
    registry.refresh()
    result = registry.list_datasets()
    assert [d.dataset_id for d in result] == ["dataset-a"]
    assert result[0].replicas[0].source_ip == "new-host"
    assert "new-a" in result[0].tags
    assert "匹配到 0 个连接器" in caplog.text


def test_source_name_does_not_route_disabled_connector_as_available(catalog):
    registry, connectors, datasets = catalog
    connectors[0]["enabled"] = False
    assert registry.list_datasets()[0].replicas[0].status == "DISABLED"


def test_source_name_without_execution_location_is_skipped(catalog, caplog):
    registry, connectors, datasets = catalog
    connectors[0].pop("serviceUrl")
    assert [d.dataset_id for d in registry.list_datasets()] == ["dataset-b"]
    assert "没有可用执行位置" in caplog.text
