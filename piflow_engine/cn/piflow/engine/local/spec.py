from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ParameterSpec:
    name: str
    role: str = "config"
    type: str = "string"
    required: bool = False
    description: str = ""
    default: Any = None


@dataclass(frozen=True)
class CommandSpec:
    name: str
    version: str = ""
    description: str = ""
    language: str = ""
    script_path: str = ""
    entrypoint: str = ""
    command_template: tuple[str, ...] = ()
    input_params: tuple[ParameterSpec, ...] = ()
    output_params: tuple[ParameterSpec, ...] = ()
    source: str = ""
    base_dir: Path = field(default_factory=Path)

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
        *,
        source: str = "",
        base_dir: Path | None = None,
    ) -> "CommandSpec":
        root_dir = base_dir or Path.cwd()
        return cls(
            name=str(data.get("name", "")),
            version=str(data.get("version", "")),
            description=str(data.get("description", "")),
            language=str(data.get("language", "")),
            script_path=str(data.get("script_path", "")),
            entrypoint=str(data.get("entrypoint", "")),
            command_template=tuple(str(item) for item in data.get("command_template", [])),
            input_params=tuple(_param_list(data.get("input_params", []))),
            output_params=tuple(_param_list(data.get("output_params", []))),
            source=source,
            base_dir=root_dir,
        )


def _param_list(raw_items: list[dict[str, Any]]) -> list[ParameterSpec]:
    return [
        ParameterSpec(
            name=str(item.get("name", "")),
            role=str(item.get("role", "config")),
            type=str(item.get("type", "string")),
            required=bool(item.get("required", False)),
            description=str(item.get("description", "")),
            default=item.get("default"),
        )
        for item in raw_items
    ]
