"""Configuration loading for the chemical runtime package."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

import yaml


class ChemicalConfigError(ValueError):
    """Raised when a chemical runtime configuration is invalid."""


@dataclass(frozen=True)
class ChemicalNode:
    """A compute node available to chemical workflow execution."""

    name: str
    ip: str
    port: int
    software: tuple[str, ...]


@dataclass(frozen=True)
class ChemicalMainNode:
    """The chemical main node used for orchestration, not persisted."""

    ip: str
    port: int


@dataclass(frozen=True)
class ChemicalConfig:
    """The chemical runtime configuration."""

    main_node: ChemicalMainNode
    nodes: tuple[ChemicalNode, ...]

    @classmethod
    def from_mapping(cls, raw_config: Mapping[str, Any]) -> "ChemicalConfig":
        if not isinstance(raw_config, Mapping):
            raise ChemicalConfigError("configuration root must be an object")

        raw_main_node = raw_config.get("main_node")
        if not isinstance(raw_main_node, Mapping):
            raise ChemicalConfigError(
                "configuration field 'main_node' must be an object"
            )
        main_node = _parse_main_node(raw_main_node)

        raw_nodes = raw_config.get("nodes")
        if not isinstance(raw_nodes, list):
            raise ChemicalConfigError("configuration field 'nodes' must be a list")
        if not raw_nodes:
            raise ChemicalConfigError("configuration field 'nodes' must not be empty")

        nodes = tuple(
            _parse_node(raw_node, index=index)
            for index, raw_node in enumerate(raw_nodes)
        )
        _ensure_unique_node_names(nodes)
        return cls(main_node=main_node, nodes=nodes)

    @classmethod
    def from_file(cls, config_path: str | Path) -> "ChemicalConfig":
        path = Path(config_path)
        if not path.is_file():
            raise FileNotFoundError(f"chemical configuration file not found: {path}")

        raw_config = _read_config_file(path)
        return cls.from_mapping(raw_config)

    def get_node(self, name: str) -> ChemicalNode:
        """Return a node by name."""

        for node in self.nodes:
            if node.name == name:
                return node
        raise KeyError(f"chemical node not found: {name}")


def load_chemical_config(config_path: str | Path) -> ChemicalConfig:
    """Load and validate a chemical runtime configuration file."""

    return ChemicalConfig.from_file(config_path)


def _read_config_file(path: Path) -> Mapping[str, Any]:
    suffix = path.suffix.lower()
    try:
        with path.open("r", encoding="utf-8") as config_file:
            if suffix == ".json":
                raw_config = json.load(config_file)
            elif suffix in {".yaml", ".yml"}:
                raw_config = yaml.safe_load(config_file)
            else:
                raise ChemicalConfigError(
                    "unsupported configuration format; use .json, .yaml, or .yml"
                )
    except (json.JSONDecodeError, yaml.YAMLError) as exc:
        raise ChemicalConfigError(f"failed to parse configuration file: {path}") from exc

    if raw_config is None:
        raise ChemicalConfigError("configuration file must not be empty")
    return raw_config


def _parse_node(raw_node: Any, *, index: int) -> ChemicalNode:
    if not isinstance(raw_node, Mapping):
        raise ChemicalConfigError(f"node at index {index} must be an object")

    name = _required_string(raw_node, "name", index=index)
    ip = _required_string(raw_node, "ip", index=index)

    raw_port = raw_node.get("port")
    if isinstance(raw_port, bool) or not isinstance(raw_port, int):
        raise ChemicalConfigError(f"node '{name}' field 'port' must be an integer")
    if not 1 <= raw_port <= 65535:
        raise ChemicalConfigError(
            f"node '{name}' field 'port' must be between 1 and 65535"
        )

    raw_software = raw_node.get("software")
    if not isinstance(raw_software, (list, tuple, set)):
        raise ChemicalConfigError(
            f"node '{name}' field 'software' must be a string collection"
        )
    software = tuple(raw_software)
    if any(not isinstance(item, str) or not item.strip() for item in software):
        raise ChemicalConfigError(
            f"node '{name}' field 'software' must contain non-empty strings"
        )

    return ChemicalNode(name=name, ip=ip, port=raw_port, software=software)


def _parse_main_node(raw_node: Mapping[str, Any]) -> ChemicalMainNode:
    ip = raw_node.get("ip")
    if not isinstance(ip, str) or not ip.strip():
        raise ChemicalConfigError(
            "main_node field 'ip' must be a non-empty string"
        )

    raw_port = raw_node.get("port")
    if isinstance(raw_port, bool) or not isinstance(raw_port, int):
        raise ChemicalConfigError("main_node field 'port' must be an integer")
    if not 1 <= raw_port <= 65535:
        raise ChemicalConfigError(
            "main_node field 'port' must be between 1 and 65535"
        )

    return ChemicalMainNode(ip=ip.strip(), port=raw_port)


def _required_string(raw_node: Mapping[str, Any], field_name: str, *, index: int) -> str:
    value = raw_node.get(field_name)
    if not isinstance(value, str) or not value.strip():
        raise ChemicalConfigError(
            f"node at index {index} field '{field_name}' must be a non-empty string"
        )
    return value.strip()


def _ensure_unique_node_names(nodes: tuple[ChemicalNode, ...]) -> None:
    names = [node.name for node in nodes]
    if len(names) != len(set(names)):
        raise ChemicalConfigError("node names must be unique")
