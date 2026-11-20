"""Connector identities resolve through public service calls without network I/O."""
from copy import deepcopy

import pytest

from services import corpus_connector_service as service


def connector(identifier, name, *, enabled=True):
    return {"connectorId": identifier, "name": name, "enabled": enabled,
        "institution": "Institution " + identifier, "host": "127.0.0.1"}


@pytest.fixture
def isolated_connectors(monkeypatch):
    def unexpected_network(*args, **kwargs):
        pytest.fail("Connector acceptance tests must not access the network")

    monkeypatch.setattr(service.requests.sessions.Session, "request", unexpected_network)

    def install(connectors, references):
        data = {"id": "dataset-1", "cstr": "dataset-1", "title": "Observation records",
            "fromList": deepcopy(references)}
        calls = {"snapshot": [], "datasets": [], "resources": []}

        def snapshot(**kwargs):
            calls["snapshot"].append(kwargs)
            return {"data": {"content": deepcopy(connectors), "total": len(connectors)}}

        def datasets(**kwargs):
            calls["datasets"].append(deepcopy(kwargs))
            return {"data": {"content": [deepcopy(data)], "total": 1}}

        def resource(target):
            calls["resources"].append(target)
            return {"cpu_cores": 4, "memory_gb": 8, "free_disk_gb": 20,
                "hostname": "worker", "latency_ms": 1}

        monkeypatch.setattr(service, "_fetch_connector_page", snapshot)
        monkeypatch.setattr(service, "_fetch_dataset_page", datasets)
        monkeypatch.setattr(service, "_fetch_dataset_detail", lambda identifier: deepcopy(data))
        monkeypatch.setattr(service, "_fetch_remote_resource", resource)
        return calls

    return install


@pytest.mark.parametrize("reference", ["node-a", {"connectorId": "node-a"}, "Archive A"])
@pytest.mark.parametrize("entrypoint", ["list", "detail"])
def test_connector_id_and_name_shapes_resolve_to_one_canonical_identity(isolated_connectors, reference, entrypoint):
    calls = isolated_connectors([connector("node-a", "Archive A")], [reference])
    result = (service.list_dataset_details()["items"][0] if entrypoint == "list"
        else service.get_dataset_detail("dataset-1"))
    assert result["replicaCount"] == 1
    assert result["connectors"][0]["connectorId"] == "node-a"
    assert result["connectors"][0]["name"] == "Archive A"
    assert result["connectors"][0]["connectorOrganization"] == "Institution node-a"
    assert result["connectors"][0]["status"] == "可用"
    assert len(calls["snapshot"]) == 1 and len(calls["resources"]) == 1


def test_explicit_id_wins_over_another_connectors_same_name(isolated_connectors):
    calls = isolated_connectors([
        connector("node-a", "Archive A"), connector("node-b", "node-a"),
    ], [{"connectorId": "node-a", "name": "node-a"}])
    result = service.list_dataset_details()["items"][0]
    assert result["connectors"][0]["connectorId"] == "node-a"
    assert result["connectors"][0]["name"] == "Archive A"
    assert len(calls["resources"]) == 1


def test_resolved_id_and_name_aliases_share_one_replica_and_resource_call(isolated_connectors):
    calls = isolated_connectors([connector("node-a", "Archive A")],
        ["node-a", "Archive A", {"connectorId": "node-a"}])
    result = service.list_dataset_details()["items"][0]
    assert result["replicaCount"] == 1 and len(result["connectors"]) == 1
    assert result["connectorId"] == "node-a"
    assert len(calls["snapshot"]) == 1 and len(calls["resources"]) == 1


def test_distinct_case_sensitive_ids_survive_snapshot_and_reference_normalization(isolated_connectors):
    calls = isolated_connectors([
        connector("Node-A", "Upper archive"), connector("node-a", "Lower archive"),
    ], [{"connectorId": "Node-A"}, {"connectorId": "node-a"}])
    result = service.list_dataset_details()["items"][0]
    assert result["replicaCount"] == 2
    assert {row["connectorId"]: row["name"] for row in result["connectors"]} == {
        "Node-A": "Upper archive", "node-a": "Lower archive"}
    assert all(row["status"] == "可用" for row in result["connectors"])
    assert len(calls["resources"]) == 2


def test_ambiguous_name_is_not_bound_to_arbitrary_connector(isolated_connectors):
    calls = isolated_connectors([
        connector("node-a", "Shared archive"), connector("node-b", "Shared archive"),
    ], [{"name": "Shared archive"}])
    result = service.list_dataset_details()["items"][0]
    assert result["connectors"][0]["status"] == "不可用"
    assert not result["connectors"][0]["connectorOrganization"]
    assert result["connectors"][0]["connectorId"] not in {"node-a", "node-b"}
    assert not calls["resources"]


def test_explicit_ids_resolve_both_connectors_with_the_same_name(isolated_connectors):
    calls = isolated_connectors([
        connector("node-a", "Shared archive"), connector("node-b", "Shared archive"),
    ], [{"connectorId": "node-a"}, {"connectorId": "node-b"}])
    result = service.list_dataset_details()["items"][0]
    assert {row["connectorId"] for row in result["connectors"]} == {"node-a", "node-b"}
    assert all(row["status"] == "可用" for row in result["connectors"])
    assert result["replicaCount"] == 2 and len(calls["resources"]) == 2


def test_enabled_source_filter_keeps_existing_name_contract(isolated_connectors):
    calls = isolated_connectors([
        connector("node-a", "Archive A"), connector("node-b", "Archive B", enabled=False),
    ], ["node-a"])
    service.list_dataset_details(filters={"keyword": "observations"})
    assert calls["datasets"][0]["filters"] == {"keyword": "observations", "sources": ["Archive A"]}
    assert len(calls["snapshot"]) == 1


def test_disabled_same_name_is_counted_once_in_available_total(isolated_connectors, monkeypatch):
    calls = isolated_connectors([
        connector("node-a", "Shared archive", enabled=False),
        connector("node-b", "Shared archive", enabled=False),
    ], [])

    def datasets(**kwargs):
        calls["datasets"].append(kwargs)
        return {"data": {"content": [], "total": 10 if not kwargs.get("filters") else 3}}

    monkeypatch.setattr(service, "_fetch_dataset_page", datasets)
    assert service.get_available_dataset_total() == 7
    assert [call.get("filters") for call in calls["datasets"]] == [None, {"sources": ["Shared archive"]}]
    assert len(calls["snapshot"]) == 1 and not calls["resources"]


@pytest.mark.parametrize("entrypoint", ["list", "detail"])
def test_unknown_explicit_id_does_not_bind_to_its_known_name(isolated_connectors, entrypoint):
    calls = isolated_connectors([connector("known", "Archive")], [{"connectorId": "unknown", "name": "Archive"}])
    result = service.list_dataset_details()["items"][0] if entrypoint == "list" else service.get_dataset_detail("dataset-1")
    assert result["connectors"][0]["connectorId"] == "unknown"
    assert result["connectors"][0]["status"] == "不可用"
    assert not calls["resources"]


@pytest.mark.parametrize("reference,identifier", [("node-a", "node-a"), ({"name": "node-a"}, "node-b")])
def test_bare_reference_prefers_id_while_explicit_name_resolves_as_name(isolated_connectors, reference, identifier):
    calls = isolated_connectors([connector("node-a", "Archive"), connector("node-b", "node-a")], [reference])
    result = service.get_dataset_detail("dataset-1")
    assert result["connectors"][0]["connectorId"] == identifier
    assert len(calls["resources"]) == 1


@pytest.mark.parametrize("reverse", [False, True])
def test_ambiguous_name_stays_unbound_beside_an_explicit_id(isolated_connectors, reverse):
    references = [{"name": "Shared"}, {"connectorId": "node-a"}]
    calls = isolated_connectors([connector("node-a", "Shared"), connector("node-b", "Shared")],
        list(reversed(references)) if reverse else references)
    rows = service.get_dataset_detail("dataset-1")["connectors"]
    assert len(rows) == 2
    assert {(row["connectorId"], row["status"]) for row in rows} == {("", "不可用"), ("node-a", "可用")}
    assert len(calls["resources"]) == 1


@pytest.mark.parametrize("entrypoint", ["list", "detail"])
def test_name_resolution_checks_later_snapshot_pages_for_ambiguity(isolated_connectors, monkeypatch, entrypoint):
    calls = isolated_connectors([], [{"name": "Shared"}])
    pages = [[connector("first", "Shared"), *[connector(str(index), "Other " + str(index)) for index in range(99)]],
        [connector("second", "Shared")]]
    def snapshot(**kwargs):
        calls["snapshot"].append(kwargs)
        return {"data": {"content": pages[kwargs["page_num"] - 1], "total": 101}}
    monkeypatch.setattr(service, "_fetch_connector_page", snapshot)
    result = service.list_dataset_details()["items"][0] if entrypoint == "list" else service.get_dataset_detail("dataset-1")
    assert result["connectors"][0]["status"] == "不可用"
    assert not calls["resources"]
    assert [item["page_num"] for item in calls["snapshot"]] == [1, 2]


@pytest.mark.parametrize("enabled_first", [False, True])
def test_shared_enabled_source_name_is_not_subtracted_from_available_total(isolated_connectors, monkeypatch, enabled_first):
    entries = [connector("enabled", "Shared", enabled=True), connector("disabled", "Shared", enabled=False)]
    calls = isolated_connectors(entries if enabled_first else list(reversed(entries)), [])
    def datasets(**kwargs):
        calls["datasets"].append(kwargs)
        return {"data": {"content": [], "total": 10 if not kwargs.get("filters") else 3}}
    monkeypatch.setattr(service, "_fetch_dataset_page", datasets)
    assert service.get_available_dataset_total() == 10
    assert [call.get("filters") for call in calls["datasets"]] == [None]


def test_resource_entrypoint_resolves_wrapped_connector_without_a_second_probe(isolated_connectors):
    calls = isolated_connectors([connector("node-a", "Archive A")], [{"connectorId": "node-a"}])
    result = service.get_dataset_connector_detail_with_resource("dataset-1")
    row, = result["dataset"]["connectors"]
    assert (row["connectorId"], row["name"], row["status"]) == ("node-a", "Archive A", "可用")
    assert row["connectorOrganization"] == "Institution node-a"
    assert len(calls["snapshot"]) == len(calls["resources"]) == 1
