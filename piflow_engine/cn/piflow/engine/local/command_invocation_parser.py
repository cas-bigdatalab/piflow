from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from piflow_engine.cn.piflow.core.stream import JobInputStream
from piflow_engine.cn.piflow.engine.local.spec import CommandSpec, ParameterSpec

## 123

@dataclass(frozen=True)
class CommandInvocation:
    command: list[str]
    resolved_values: dict[str, str]
    input_keys: tuple[str, ...]
    output_keys: tuple[str, ...]
    runtime_properties: dict[str, str]
    output_files: dict[str, str]


_SKIP_TOKEN = object()
_STRINGIFIED_FILE_ARTIFACT_PATH_PATTERN = re.compile(r"path='([^']+)'")


class CommandInvocationParser:
    def __init__(self, spec: CommandSpec) -> None:
        self.spec = spec
        self._validate_command_template()

    def parse(
        self,
        inputs: JobInputStream,
        workspace: Path,
        properties: dict[str, Any],
    ) -> CommandInvocation:
        values: dict[str, str | object] = {
            "script_path": str((self.spec.base_dir / self.spec.script_path).resolve())
        }
        input_keys: list[str] = []
        output_keys: list[str] = []
        runtime_properties: dict[str, str] = {}
        output_files: dict[str, str] = {}
        output_params_by_name = {
            parameter.name: parameter
            for parameter in self.spec.output_params
            if _is_output_data(parameter)
        }

        for parameter in self.spec.input_params:
            if _is_input_data(parameter):
                input_keys.append(parameter.name)
                values[parameter.name] = self._input_path(parameter, inputs)
                continue

            if _is_output_data(parameter):
                output_param = output_params_by_name.get(parameter.name, parameter)
                output_path = self._output_path(output_param, workspace)
                values[parameter.name] = output_path
                output_files[parameter.name] = output_path
                if parameter.name not in output_keys:
                    output_keys.append(parameter.name)
                continue

            value = self._runtime_value(parameter, properties, workspace)
            values[parameter.name] = value
            if value is not _SKIP_TOKEN:
                runtime_properties[parameter.name] = value

        for parameter in self.spec.output_params:
            if not _is_output_data(parameter):
                continue
            output_path = values.get(parameter.name)
            if output_path is None:
                output_path = self._output_path(parameter, workspace)
                values[parameter.name] = output_path
            output_files[parameter.name] = output_path
            if parameter.name not in output_keys:
                output_keys.append(parameter.name)

        return CommandInvocation(
            command=self._render_command(values),
            resolved_values={
                key: value for key, value in values.items() if value is not _SKIP_TOKEN
            },
            input_keys=tuple(input_keys),
            output_keys=tuple(output_keys),
            runtime_properties=runtime_properties,
            output_files=output_files,
        )

    def _input_path(self, parameter: ParameterSpec, inputs: JobInputStream) -> str:
        if not inputs.contains(parameter.name):
            if parameter.required:
                raise ValueError(f"missing required input data: {parameter.name}")
            return ""

        artifact = inputs.read(parameter.name)
        path = getattr(artifact, "path", "") or str(getattr(artifact, "value", ""))
        if isinstance(path, str):
            path = self._coerce_stringified_file_artifact_path(path)
        if not path:
            raise ValueError(f"input artifact for port '{parameter.name}' has no file path")
        return path

    def _runtime_value(
        self,
        parameter: ParameterSpec,
        properties: dict[str, Any],
        workspace: Path,
    ) -> str | object:
        if parameter.name in properties:
            return str(properties[parameter.name])

        if parameter.default is not None:
            return str(parameter.default)

        # Backward compatibility for old skill.json files that modelled output
        # paths as plain data/runtime parameters.
        if parameter.name.startswith("output"):
            return self._output_path(parameter, workspace)

        if parameter.required:
            raise ValueError(f"missing required parameter: {parameter.name}")

        return _SKIP_TOKEN

    def _output_path(self, parameter: ParameterSpec, workspace: Path) -> str:
        if parameter.default:
            output_path = Path(str(parameter.default))
            if output_path.is_absolute():
                return str(output_path)
            return str((workspace / "output" / output_path).resolve())

        suffix = _guess_suffix(parameter.type)
        return str((workspace / "output" / f"{parameter.name}{suffix}").resolve())

    def _render_command(self, values: dict[str, str | object]) -> list[str]:
        command: list[str] = []
        tokens = self.spec.command_template
        index = 0
        while index < len(tokens):
            token = tokens[index]
            if (
                index + 1 < len(tokens)
                and token.startswith("-")
                and _placeholder_name(tokens[index + 1]) is not None
            ):
                key = _placeholder_name(tokens[index + 1])
                assert key is not None
                value = values.get(key, "")
                if value is _SKIP_TOKEN:
                    index += 2
                    continue

            rendered = token
            for key, value in values.items():
                if value is _SKIP_TOKEN:
                    continue
                rendered = rendered.replace(f"{{{key}}}", value)
            command.append(rendered)
            index += 1
        return command

    def _validate_command_template(self) -> None:
        command_tokens = set(self.spec.command_template)
        for parameter in self.spec.input_params:
            option = f"--{parameter.name}"
            placeholder = f"{{{parameter.name}}}"
            if option not in command_tokens or placeholder not in command_tokens:
                raise ValueError(
                    f"parameter '{parameter.name}' must match command_template "
                    f"tokens '{option}' and '{placeholder}'"
                )

    @staticmethod
    def _coerce_stringified_file_artifact_path(value: str) -> str:
        # TEMP production patch: remove after the DAG/runtime path always passes
        # real FileArtifact.path values instead of `str(FileArtifact(...))`.
        if not value.startswith("FileArtifact("):
            return value

        match = _STRINGIFIED_FILE_ARTIFACT_PATH_PATTERN.search(value)
        if match is None:
            return value
        return match.group(1)


def _role(parameter: ParameterSpec) -> str:
    return parameter.role.lower()


def _is_input_data(parameter: ParameterSpec) -> bool:
    return _role(parameter) == "input_data"


def _is_output_data(parameter: ParameterSpec) -> bool:
    return _role(parameter) == "output_data"


def _guess_suffix(param_type: str) -> str:
    normalized = param_type.lower()
    if normalized in {"csv_file", "csv"}:
        return ".csv"
    if normalized in {"json_file", "json"}:
        return ".json"
    if normalized in {"txt", "text", "text_file"}:
        return ".txt"
    if normalized in {"xlsx", "excel", "excel_file"}:
        return ".xlsx"
    return ""


def _placeholder_name(token: str) -> str | None:
    if token.startswith("{") and token.endswith("}"):
        return token[1:-1]
    return None
