from pathlib import Path

import pytest

from chemical import (
    ChemicalConfig,
    ChemicalConfigError,
    load_chemical_config,
)


def test_load_chemical_config_from_yaml(tmp_path: Path) -> None:
    config_path = tmp_path / "chemical.yaml"
    config_path.write_text(
        """
main_node:
  ip: 10.0.87.110
  port: 50061
nodes:
  - name: node-a
    ip: 10.0.0.10
    port: 50051
    software: [Gaussian, Multiwfn]
""",
        encoding="utf-8",
    )

    config = load_chemical_config(config_path)

    assert config.get_node("node-a").ip == "10.0.0.10"
    assert config.get_node("node-a").port == 50051
    assert config.get_node("node-a").software == ("Gaussian", "Multiwfn")
    assert config.main_node.ip == "10.0.87.110"
    assert config.main_node.port == 50061


def test_load_chemical_config_from_json(tmp_path: Path) -> None:
    config_path = tmp_path / "chemical.json"
    config_path.write_text(
        '{"main_node": {"ip": "10.0.87.110", "port": 50061}, '
        '"nodes": [{"name": "node-a", "ip": "127.0.0.1", '
        '"port": 50051, "software": ["Gaussian"]}]}',
        encoding="utf-8",
    )

    config = ChemicalConfig.from_file(config_path)

    assert len(config.nodes) == 1
    assert config.nodes[0].name == "node-a"


@pytest.mark.parametrize(
    "config",
    [
        {
            "main_node": {"ip": "127.0.0.1", "port": 50061},
            "nodes": [],
        },
        {"nodes": []},
        {
            "main_node": {"ip": "127.0.0.1", "port": 50061},
            "nodes": [
                {
                    "name": "node-a",
                    "ip": "127.0.0.1",
                    "port": 0,
                    "software": ["Gaussian"],
                }
            ]
        },
        {
            "main_node": {"ip": "127.0.0.1", "port": 50061},
            "nodes": [
                {
                    "name": "node-a",
                    "ip": "127.0.0.1",
                    "port": 50051,
                    "software": ["Gaussian", 123],
                }
            ]
        },
    ],
)
def test_invalid_chemical_config_is_rejected(config: dict) -> None:
    with pytest.raises(ChemicalConfigError):
        ChemicalConfig.from_mapping(config)
