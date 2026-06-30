from __future__ import annotations

import importlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from piflow_engine.cn.piflow.core.stop import ConfigurableStop
from piflow_engine.cn.piflow.engine.local.command_invocation_parser import CommandInvocationParser
from piflow_engine.cn.piflow.engine.local.command_stop import CommandStop
from piflow_engine.cn.piflow.engine.local.resolver import FileBundleResolver


@dataclass
class StopBean:

    flow_name: str = ""
    uuid: str = ""
    name: str = ""
    bundle: str = ""
    properties: dict[str, Any] = field(default_factory=dict)
    customized_properties: dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, flow_name: str, data: dict[str, Any]) -> "StopBean":
        return cls(
            flow_name=flow_name,
            uuid=str(data.get("uuid", "")),
            name=str(data.get("name", "")),
            bundle=str(data.get("bundle", "")),
            properties=dict(data.get("properties", {})),
            customized_properties=dict(data.get("customizedProperties", {})),
        )

    def construct_stop(self) -> ConfigurableStop:
        stop = self._load_stop()
        setattr(stop, "piflow_stop_uuid", self.uuid)
        setattr(stop, "piflow_stop_name", self.name)
        setattr(stop, "piflow_bundle", self.bundle)
        stop.set_properties(self.properties)
        stop.set_customized_properties(self.customized_properties)
        return stop

    def _load_stop(self) -> ConfigurableStop:
        if not self.bundle:
            raise ValueError("stop bundle must not be empty")

        if self._looks_like_command_bundle():
            return self._load_command_stop()

        module_name, _, class_name = self.bundle.rpartition(".")
        if not module_name or not class_name:
            raise ValueError(f"invalid stop bundle: {self.bundle}")

        module = importlib.import_module(module_name)
        stop_class = getattr(module, class_name)
        stop = stop_class()

        if not isinstance(stop, ConfigurableStop) and not self._is_compatible_configurable_stop(stop):
            raise TypeError(
                f"stop class '{self.bundle}' must inherit from ConfigurableStop"
            )

        return stop

    def _load_command_stop(self) -> ConfigurableStop:
        resolver = FileBundleResolver()
        spec = resolver.resolve(self.bundle)
        parser = CommandInvocationParser(spec)
        return CommandStop(parser)

    def _looks_like_command_bundle(self) -> bool:
        bundle_path = Path(self.bundle)
        return bundle_path.suffix.lower() == ".json" or bundle_path.exists()

    @staticmethod
    def _is_compatible_configurable_stop(stop: object) -> bool:
        # TEMP production patch: remove after all runtime imports consistently
        # resolve `ConfigurableStop` from a single module namespace.
        return any(cls.__name__ == "ConfigurableStop" for cls in type(stop).__mro__)
