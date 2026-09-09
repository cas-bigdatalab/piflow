from __future__ import annotations

from pathlib import Path

from chemical.service import ChemicalNodeResourceService


class _FakeClient:
    def __init__(self, response=None, error: Exception | None = None):
        self.response = response
        self.error = error
        self.closed = False

    def get_server_resource(self):
        if self.error is not None:
            raise self.error
        return self.response

    def close(self) -> None:
        self.closed = True


class _FakeResponse:
    def __init__(self, cpu_cores: float, memory_gb: float, free_disk_gb: float, hostname: str):
        self.cpu_cores = cpu_cores
        self.memory_gb = memory_gb
        self.free_disk_gb = free_disk_gb
        self.hostname = hostname


def test_chemical_node_resource_service_refreshes_nodes(tmp_path: Path) -> None:
    config_path = tmp_path / "chemical.yaml"
    config_path.write_text(
        """
main_node:
  ip: 10.0.87.110
  port: 50061
nodes:
  - name: node-a
    ip: 10.0.0.1
    port: 50061
    software: [Gaussian, Multiwfn]
  - name: node-b
    ip: 10.0.0.2
    port: 50062
    software: [OpenBabel]
""",
        encoding="utf-8",
    )

    clients: dict[str, _FakeClient] = {
        "10.0.0.1:50061": _FakeClient(_FakeResponse(8.0, 16.0, 100.0, "host-a")),
        "10.0.0.2:50062": _FakeClient(_FakeResponse(4.0, 8.0, 50.0, "host-b")),
    }

    service = ChemicalNodeResourceService(config_path, client_factory=clients.__getitem__)

    table = service.refresh()

    assert [row.name for row in table] == ["node-a", "node-b"]
    assert service.get_node("node-a").cpu_cores == 8.0
    assert service.get_node("node-b").memory_gb == 8.0
    assert clients["10.0.0.1:50061"].closed is True
    assert clients["10.0.0.2:50062"].closed is True


def test_chemical_node_resource_service_keeps_failed_node_snapshot(tmp_path: Path) -> None:
    config_path = tmp_path / "chemical.yaml"
    config_path.write_text(
        """
main_node:
  ip: 10.0.87.110
  port: 50061
nodes:
  - name: node-a
    ip: 10.0.0.1
    port: 50061
    software: [Gaussian]
""",
        encoding="utf-8",
    )

    service = ChemicalNodeResourceService(
        config_path,
        client_factory=lambda target: _FakeClient(error=RuntimeError(f"boom:{target}")),
    )

    table = service.refresh()

    assert table[0].status == "unreachable"
    assert "boom:10.0.0.1:50061" in table[0].error_message
    assert table[0].software == ("Gaussian",)


def test_chemical_service_builds_software_instance_table(tmp_path: Path) -> None:
    config_path = tmp_path / "chemical.yaml"
    config_path.write_text(
        """
main_node:
  ip: 10.0.87.110
  port: 50061
nodes:
  - name: node-a
    ip: 10.0.0.1
    port: 50061
    software: [Gaussian, Multiwfn]
  - name: node-b
    ip: 10.0.0.2
    port: 50062
    software: [OpenBabel, Gaussian]
""",
        encoding="utf-8",
    )

    service = ChemicalNodeResourceService(
        config_path,
        client_factory=lambda target: _FakeClient(_FakeResponse(1.0, 2.0, 3.0, target)),
    )

    assert service.list_software_columns() == ("Gaussian", "Multiwfn", "OpenBabel")
    assert service.list_software_instance_table()[0].instances == {
        "Gaussian": 0,
        "Multiwfn": 0,
        "OpenBabel": 0,
    }
    assert service.list_software_instance_table()[1].instances == {
        "Gaussian": 0,
        "Multiwfn": 0,
        "OpenBabel": 0,
    }


def test_chemical_service_updates_software_instance_count(tmp_path: Path) -> None:
    config_path = tmp_path / "chemical.yaml"
    config_path.write_text(
        """
main_node:
  ip: 10.0.87.110
  port: 50061
nodes:
  - name: node-a
    ip: 10.0.0.1
    port: 50061
    software: [Gaussian]
""",
        encoding="utf-8",
    )

    service = ChemicalNodeResourceService(
        config_path,
        client_factory=lambda target: _FakeClient(_FakeResponse(1.0, 2.0, 3.0, target)),
    )

    service.set_software_instance_count("node-a", "Gaussian", 2)
    service.increment_software_instance_count("node-a", "Gaussian")

    assert service.list_software_instance_table()[0].instances["Gaussian"] == 3


def test_chemical_service_has_software_and_change_count(tmp_path: Path) -> None:
    config_path = tmp_path / "chemical.yaml"
    config_path.write_text(
        """
main_node:
  ip: 10.0.87.110
  port: 50061
nodes:
  - name: node-a
    ip: 10.0.0.1
    port: 50061
    software: [Gaussian, Multiwfn]
""",
        encoding="utf-8",
    )

    service = ChemicalNodeResourceService(
        config_path,
        client_factory=lambda target: _FakeClient(_FakeResponse(1.0, 2.0, 3.0, target)),
    )

    assert service.has_software("node-a", "Gaussian") is True
    assert service.has_software("node-a", "OpenBabel") is False

    service.change_software_instance_count("node-a", "Gaussian", 2)
    assert service.list_software_instance_table()[0].instances["Gaussian"] == 2

    service.change_software_instance_count("node-a", "Gaussian", -1)
    assert service.list_software_instance_table()[0].instances["Gaussian"] == 1


def test_chemical_service_rejects_negative_software_instance_count(tmp_path: Path) -> None:
    config_path = tmp_path / "chemical.yaml"
    config_path.write_text(
        """
main_node:
  ip: 10.0.87.110
  port: 50061
nodes:
  - name: node-a
    ip: 10.0.0.1
    port: 50061
    software: [Gaussian]
""",
        encoding="utf-8",
    )

    service = ChemicalNodeResourceService(
        config_path,
        client_factory=lambda target: _FakeClient(_FakeResponse(1.0, 2.0, 3.0, target)),
    )

    service.set_software_instance_count("node-a", "Gaussian", 0)

    try:
        service.change_software_instance_count("node-a", "Gaussian", -1)
    except ValueError:
        pass
    else:  # pragma: no cover - defensive
        raise AssertionError("expected ValueError")
