from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
import uuid
from pathlib import Path
from typing import Any, Protocol

from piflow_engine.cn.piflow.core.artifact import FileArtifact
from piflow_engine.cn.piflow.core.runtime_context import JobContext, ProcessContext
from piflow_engine.cn.piflow.core.runtime_keys import RUN_CONTEXT_FINAL_OUTPUT_PATH
from piflow_engine.cn.piflow.core.stop import ConfigurableStop
from piflow_engine.cn.piflow.core.stream import DEFAULT_PORT, JobInputStream, JobOutputStream
from piflow_engine.cn.piflow.engine.local.constants import RUNNER_CONTEXT_WORKSPACE_ROOT


class LLMClient(Protocol):
    def transform_file(self, *, model: str, instruction: str, filename: str, content: str) -> str:
        ...


class OpenAICompatibleLLMClient:
    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,
        timeout_seconds: float,
        max_tokens: int | None = None,
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._timeout_seconds = timeout_seconds
        self._max_tokens = max_tokens

    def transform_file(
        self,
        *,
        model: str,
        instruction: str,
        filename: str,
        content: str,
    ) -> str:
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a file transformation assistant.",
                },
                {
                    "role": "user",
                    "content": _build_prompt(
                        instruction=instruction,
                        filename=filename,
                        content=content,
                    ),
                },
            ],
        }
        if self._max_tokens is not None:
            payload["max_tokens"] = self._max_tokens
        request = urllib.request.Request(
            url=f"{self._base_url}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
                "User-Agent": "piflow-piflow_engine/0.1",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(
                request,
                timeout=self._timeout_seconds,
            ) as response:
                response_payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            error_body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(
                f"llm request failed with status {exc.code}: {error_body}"
            ) from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"llm request failed: {exc.reason}") from exc

        return _extract_text_response(response_payload)


class LLMFileTransformStop(ConfigurableStop):
    author_email = ""
    description = "Transform one text file with an LLM and output a new file."
    inport_list = [DEFAULT_PORT]
    outport_list = [DEFAULT_PORT]

    client_factory = None

    def __init__(self) -> None:
        super().__init__()
        self.instruction = ""
        self.model = ""
        self.api_key = ""
        self.base_url = "https://api.openai.com/v1"
        self.output_ext = ""
        self.timeout_seconds = 60.0
        self.max_input_chars = 100000
        self.max_output_tokens: int | None = None
        self._workspace_root: Path | None = None

    def set_properties(self, properties: dict[str, Any]) -> None:
        self.instruction = _require_non_empty_string(
            properties.get("instruction", ""),
            name="instruction",
        )
        self.model = _require_non_empty_string(
            properties.get("model", ""),
            name="model",
        )
        self.api_key = _optional_string(properties.get("api_key", ""))
        self.base_url = _optional_string(properties.get("base_url", self.base_url)) or self.base_url
        self.output_ext = _normalize_output_ext(
            _optional_string(properties.get("output_ext", ""))
        )
        self.timeout_seconds = _parse_positive_float(
            properties.get("timeout_seconds", self.timeout_seconds),
            name="timeout_seconds",
        )
        self.max_input_chars = _parse_positive_int(
            properties.get("max_input_chars", self.max_input_chars),
            name="max_input_chars",
        )
        self.max_output_tokens = _parse_optional_positive_int(
            properties.get("max_output_tokens", None),
            name="max_output_tokens",
        )

    def initialize(self, ctx: ProcessContext) -> None:
        workspace_root = ctx.get(RUNNER_CONTEXT_WORKSPACE_ROOT, ".piflow/workspace")
        self._workspace_root = Path(str(workspace_root)).expanduser().resolve()
        self._workspace_root.mkdir(parents=True, exist_ok=True)

    def perform(
        self,
        inputs: JobInputStream,
        outputs: JobOutputStream,
        ctx: JobContext,
    ) -> None:
        source_path = self._read_input_file(inputs)
        content = source_path.read_text(encoding="utf-8")
        if len(content) > self.max_input_chars:
            raise ValueError(
                f"input file exceeds max_input_chars={self.max_input_chars}: {source_path}"
            )

        client = self._create_client()
        transformed = client.transform_file(
            model=self.model,
            instruction=self.instruction,
            filename=source_path.name,
            content=content,
        )
        cleaned = _strip_code_fence(transformed)
        output_path = self._prepare_output_path(ctx, source_path)
        output_path.write_text(cleaned, encoding="utf-8")

        ctx.put(RUN_CONTEXT_FINAL_OUTPUT_PATH, str(output_path))
        outputs.write(FileArtifact(path=str(output_path)))

    def _create_client(self) -> LLMClient:
        factory = type(self).client_factory
        if callable(factory):
            return factory(self)

        api_key = self.api_key or os.getenv("OPENAI_API_KEY", "")
        if not api_key:
            raise ValueError("llm api_key must not be empty")
        base_url = self.base_url or os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        return OpenAICompatibleLLMClient(
            api_key=api_key,
            base_url=base_url,
            timeout_seconds=self.timeout_seconds,
            max_tokens=self.max_output_tokens,
        )

    def _read_input_file(self, inputs: JobInputStream) -> Path:
        artifact = inputs.read() if inputs.contains() else _read_single_input(inputs)
        path = getattr(artifact, "path", "")
        raw_value = getattr(artifact, "value", "")
        if not path and isinstance(raw_value, str):
            path = raw_value
        if not path:
            raise ValueError("llm file transform input artifact has no file path")

        source_path = Path(path).expanduser().resolve()
        if not source_path.exists():
            raise FileNotFoundError(
                f"llm file transform input file not found: {source_path}"
            )
        if not source_path.is_file():
            raise ValueError(
                f"llm file transform input path is not a file: {source_path}"
            )
        if source_path.suffix.lower() not in _TEXT_FILE_EXTENSIONS:
            raise ValueError(
                f"llm file transform only supports text files, got: {source_path.suffix}"
            )
        return source_path

    def _prepare_output_path(self, ctx: JobContext, source_path: Path) -> Path:
        if self._workspace_root is None:
            raise RuntimeError("workspace root is not initialized")

        process_id = ctx.get_process_context().get_process().pid()
        stop_name = ctx.get_stop_job().get_stop_name()
        job_id = ctx.get_stop_job().jid()
        output_dir = (
            self._workspace_root
            / process_id
            / f"{stop_name}_{job_id}_{uuid.uuid4().hex[:8]}"
            / "output"
        )
        output_dir.mkdir(parents=True, exist_ok=True)
        suffix = self.output_ext or source_path.suffix
        return output_dir / f"{source_path.stem}_transformed{suffix}"


_TEXT_FILE_EXTENSIONS = {
    ".txt",
    ".md",
    ".markdown",
    ".json",
    ".csv",
    ".html",
    ".xml",
    ".yaml",
    ".yml",
}


def _build_prompt(*, instruction: str, filename: str, content: str) -> str:
    return (
        "You are a file processing assistant.\n"
        "Please transform the file content according to the user instruction.\n"
        "Return only the full transformed file content.\n"
        "Do not add explanations.\n"
        "Do not wrap the result in code fences.\n\n"
        f"User instruction:\n{instruction}\n\n"
        f"Original filename:\n{filename}\n\n"
        f"File content:\n{content}"
    )


def _extract_text_response(payload: dict[str, Any]) -> str:
    choices = payload.get("choices")
    if not isinstance(choices, list) or not choices:
        raise RuntimeError("llm response missing choices")

    message = choices[0].get("message", {})
    content = message.get("content", "")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        text_parts: list[str] = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                text_parts.append(str(item.get("text", "")))
        if text_parts:
            return "".join(text_parts)
    raise RuntimeError("llm response missing text content")


def _strip_code_fence(text: str) -> str:
    stripped = text.strip()
    match = re.fullmatch(r"```[a-zA-Z0-9_-]*\n?(.*)\n?```", stripped, flags=re.DOTALL)
    if match is not None:
        return match.group(1).strip()
    return text


def _read_single_input(inputs: JobInputStream) -> Any:
    ports = inputs.ports()
    if len(ports) != 1:
        raise ValueError(
            f"llm file transform requires exactly one input, got ports={ports}"
        )
    return inputs.read(ports[0])


def _require_non_empty_string(value: Any, *, name: str) -> str:
    text = _optional_string(value)
    if not text:
        raise ValueError(f"{name} must not be empty")
    return text


def _optional_string(value: Any) -> str:
    if value is None:
        return ""
    if not isinstance(value, str):
        raise TypeError("string property must be a string")
    return value.strip()


def _normalize_output_ext(value: str) -> str:
    if not value:
        return ""
    return value if value.startswith(".") else f".{value}"


def _parse_positive_float(value: Any, *, name: str) -> float:
    if isinstance(value, (int, float)):
        parsed = float(value)
    elif isinstance(value, str):
        parsed = float(value.strip())
    else:
        raise TypeError(f"{name} must be a number")
    if parsed <= 0:
        raise ValueError(f"{name} must be positive")
    return parsed


def _parse_positive_int(value: Any, *, name: str) -> int:
    if isinstance(value, int):
        parsed = value
    elif isinstance(value, str):
        parsed = int(value.strip())
    else:
        raise TypeError(f"{name} must be an integer")
    if parsed <= 0:
        raise ValueError(f"{name} must be positive")
    return parsed


def _parse_optional_positive_int(value: Any, *, name: str) -> int | None:
    if value is None or value == "":
        return None
    return _parse_positive_int(value, name=name)
