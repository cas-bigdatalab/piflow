"""Connector enrichment skips malformed endpoints without network probing."""
import pytest

from services import corpus_connector_service as service


@pytest.mark.parametrize("connector,expected", [
    ({"host": "10.20.30.40"}, "10.20.30.40:50061"),
    ({"host": "worker"}, "worker:50061"),
    ({"host": "worker_1"}, "worker_1:50061"),
    ({"host": "node-2.example.org."}, "node-2.example.org.:50061"),
    ({"host": "  worker.example  "}, "worker.example:50061"),
    ({"host": "münich.example"}, "xn--mnich-kva.example:50061"),
    ({"host": "2001:db8::1"}, "[2001:db8::1]:50061"),
    ({"host": "[2001:db8::1]"}, "[2001:db8::1]:50061"),
    ({"host": "::1", "grpcPort": "65535"}, "[::1]:65535"),
    ({"host": "worker", "grpcPort": 1}, "worker:1"),
    ({"host": "worker", "grpcPort": "50062"}, "worker:50062"),
    ({"serviceUrl": "https://worker.example:8443/path?q=records"}, "worker.example:50061"),
    ({"serviceUrl": "worker_1:8081/api"}, "worker_1:50061"),
    ({"serviceUrl": "http://münich.example:8081/path"}, "xn--mnich-kva.example:50061"),
    ({"serviceUrl": "http://[2001:db8::1]:8081/api"}, "[2001:db8::1]:50061"),
    ({"serviceUrl": "2001:db8::1"}, "[2001:db8::1]:50061"),
    ({"serviceUrl": "[2001:db8::1]"}, "[2001:db8::1]:50061"),
    ({"serviceUrl": "[::1]"}, "[::1]:50061"),
    ({"serviceUrl": "[::1]:8081"}, "[::1]:50061"),
    ({"serviceUrl": "worker.example:8081", "grpcPort": "50062"}, "worker.example:50062"),
    # Explicit resolver targets belong to gRPC, not HTTP URL parsing.
    ({"remoteGrpcTarget": "dns:///worker.example:50062", "host": "-"}, "dns:///worker.example:50062"),
    ({"remoteGrpcTarget": "unix:/tmp/worker.sock"}, "unix:/tmp/worker.sock"),
    ({"remoteGrpcTarget": "10.20.30.40:50062"}, "10.20.30.40:50062"),
])
def test_valid_endpoint_enrichment_connects_once(monkeypatch, connector, expected):
    calls = []
    resource = {"hostname": "resolved-worker", "cpu_cores": 8}

    def fetch(target):
        calls.append(target)
        return resource

    monkeypatch.setattr(service, "_fetch_remote_resource", fetch)
    target, result = service._resolve_remote_resource(connector, grpc_port=50061)
    assert target == expected
    assert calls == [expected]
    assert result is resource


@pytest.mark.parametrize("connector", [
    {},
    {"host": "-"},
    {"host": "node-.example"},
    {"host": "-node.example"},
    {"host": "node..example"},
    {"host": "node example"},
    {"host": "node\nexample"},
    {"host": "node/path"},
    {"host": "node:8081"},
    {"host": "[2001:db8:::1]"},
    {"host": "a" * 64 + ".example"},
    {"serviceUrl": "-"},
    {"serviceUrl": "https://-/api"},
    {"serviceUrl": "https://node example/api"},
    {"serviceUrl": "https://node\nexample/api"},
    {"serviceUrl": "https://node.example:not-a-port/api"},
    {"serviceUrl": "https://node.example:65536/api"},
    {"serviceUrl": "https://node.example:0/api"},
    {"serviceUrl": "[::1]:65536"},
    {"serviceUrl": "http://[::1]unexpected:8081"},
    {"serviceUrl": "https://[2001:db8::1/api"},
    {"serviceUrl": "/api/data"},
    {"host": "worker", "grpcPort": "invalid"},
    {"host": "worker", "grpcPort": "50061.0"},
    {"host": "worker", "grpcPort": -1},
    {"host": "worker", "grpcPort": "0"},
    {"host": "worker", "grpcPort": "65536"},
])
def test_invalid_endpoint_returns_empty_resource_without_connection(monkeypatch, connector):
    calls = []
    monkeypatch.setattr(service, "_fetch_remote_resource", lambda target: calls.append(target))
    target, resource = service._resolve_remote_resource(connector, grpc_port=50061)
    assert calls == []
    assert target == ""
    assert resource == {"cpu_cores": None, "memory_gb": None, "free_disk_gb": None,
        "hostname": None, "latency_ms": None}


@pytest.mark.parametrize("port", [0, -1, 65536])
def test_invalid_default_port_also_skips_connection(monkeypatch, port):
    calls = []
    monkeypatch.setattr(service, "_fetch_remote_resource", lambda target: calls.append(target))
    target, resource = service._resolve_remote_resource({"host": "worker"}, grpc_port=port)
    assert calls == [] and target == ""
    assert all(value is None for value in resource.values())


@pytest.mark.parametrize("connector", [
    {"host": "256.0.0.1"}, {"host": "127.00.0.1"}, {"host": "[127.0.0.1]"},
    {"host": "worker", "grpcPort": 0}, {"host": "worker", "grpcPort": True},
    {"host": "worker", "grpcPort": False}, {"host": "worker", "grpcPort": 50061.0},
    {"host": "worker", "grpcPort": "50061\n"}, {"host": "\nworker"},
    {"serviceUrl": "https://worker.example/api\n"}, {"serviceUrl": "https://worker.example:/api"},
])
@pytest.mark.parametrize("normalize", [False, True])
def test_normalization_never_turns_invalid_endpoint_fields_into_a_probe(monkeypatch, connector, normalize):
    calls = []
    monkeypatch.setattr(service, "_fetch_remote_resource", lambda target: calls.append(target))
    candidate = service._normalize_connector_detail(connector) if normalize else connector
    target, resource = service._resolve_remote_resource(candidate, grpc_port=50061)
    assert target == "" and not calls
    assert all(value is None for value in resource.values())
