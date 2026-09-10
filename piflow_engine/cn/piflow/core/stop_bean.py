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
    output_properties: dict[str, Any] = field(default_factory=dict)
    customized_properties: dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, flow_name: str, data: dict[str, Any]) -> "StopBean":
        return cls(
            flow_name=flow_name,
            uuid=str(data.get("uuid", "")),
            name=str(data.get("name", "")),
            bundle=str(data.get("bundle", "")),
            properties=dict(data.get("properties", {})),
            output_properties=dict(
                data.get("outputProperties", data.get("output_properties", {}))
            ),
            customized_properties=dict(data.get("customizedProperties", {})),
        )

    def construct_stop(self) -> ConfigurableStop:
        stop = self._load_stop()
        setattr(stop, "piflow_stop_uuid", self.uuid)
        setattr(stop, "piflow_stop_name", self.name)
        setattr(stop, "piflow_bundle", self.bundle)
        stop.set_properties(self.properties)
        stop.set_output_properties(self.output_properties)
        stop.set_customized_properties(self.customized_properties)
        return stop

    def _load_stop(self) -> ConfigurableStop:
        if not self.bundle:
            raise ValueError("stop bundle must not be empty")

        if self._looks_like_command_bundle():
            return self._load_command_stop()

        if self._looks_like_python_bundle():
            return self._load_python_stop()

        return self._load_command_stop(self._resolve_command_bundle_path())

    def _load_python_stop(self) -> ConfigurableStop:
        module_name, _, class_name = self.bundle.rpartition(".")
        if not module_name or not class_name:
            raise ValueError(f"invalid stop bundle: {self.bundle}")

        module = importlib.import_module(module_name)
        stop_class = getattr(module, class_name)
        stop = stop_class()

        if not isinstance(stop, ConfigurableStop):
            raise TypeError(
                f"stop class '{self.bundle}' must inherit from ConfigurableStop"
            )

        return stop

    def _load_command_stop(self, bundle: str | None = None) -> ConfigurableStop:
        resolver = FileBundleResolver()
        bundle_path = bundle or self._resolve_command_bundle_path()
        spec = resolver.resolve(bundle_path)
        parser = CommandInvocationParser(spec)
        return CommandStop(parser)

    def _resolve_command_bundle_path(self) -> str:
        """Resolve either a skill.json path or a database-backed skill ID."""
        if self._looks_like_command_bundle():
            return self.bundle

        raw_skill_id = self.bundle.strip()
        if not raw_skill_id:
            raise ValueError("stop bundle must not be empty")

        try:
            from infra.config_loader import resolve_workspace_root
            from runtime.dag_manager import get_dag_skill
        except ImportError as exc:
            if self._looks_like_python_bundle():
                return self.bundle
            raise ValueError(
                f"cannot resolve skill ID '{raw_skill_id}': runtime skill lookup is unavailable"
            ) from exc

        try:
            dag_skill = get_dag_skill(raw_skill_id)
        except Exception as exc:
            if self._looks_like_python_bundle():
                return self.bundle
            raise ValueError(
                f"failed to resolve skill ID '{raw_skill_id}'"
            ) from exc

        if dag_skill is None:
            if self._looks_like_python_bundle():
                return self.bundle
            raise ValueError(f"skill ID not found: {raw_skill_id}")

        skill_path = str(getattr(dag_skill, "skill_path", "") or "").strip()
        file_path = str(getattr(dag_skill, "file_path", "") or "").strip()
        if skill_path:
            candidate = Path(skill_path).expanduser()
            if candidate.suffix.lower() != ".json":
                candidate = candidate / "skill.json"
            if not candidate.is_absolute():
                candidate = resolve_workspace_root() / candidate
            candidate = candidate.resolve()
            if candidate.is_file():
                return str(candidate)

        if file_path:
            candidate = Path(file_path).expanduser()
            if not candidate.is_absolute():
                candidate = resolve_workspace_root() / candidate
            candidate = candidate.resolve()
            if candidate.is_file() and candidate.suffix.lower() == ".json":
                return str(candidate)

        raise ValueError(
            f"skill ID '{raw_skill_id}' does not resolve to an existing skill.json "
            f"(skill_path={skill_path!r}, file_path={file_path!r})"
        )

    def _looks_like_command_bundle(self) -> bool:
        bundle_path = Path(self.bundle)
        return bundle_path.suffix.lower() == ".json" or bundle_path.exists()

    def _looks_like_python_bundle(self) -> bool:
        module_name, separator, class_name = self.bundle.rpartition(".")
        return bool(
            separator
            and module_name
            and class_name
            and class_name.isidentifier()
        )
