from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from types import ModuleType
import uuid


@dataclass(frozen=True)
class SubagentContext:
    parent_thread_id: str
    user_id: str
    request_id: str | None = None
    fork_reason: str | None = None
    context_text: str | None = None


def build_subagent_system_prompt(
    base_prompt: str,
    context_text: str | None = None,
    extra_prompt: str | None = None,
) -> str:
    parts = [base_prompt.strip()]

    if context_text:
        parts.append(context_text.strip())

    if extra_prompt:
        parts.append(extra_prompt.strip())

    return "\n\n".join(part for part in parts if part)


def build_transient_thread_id(prefix: str = "tmp") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


@contextmanager
def override_factory_prompt(
    factory_module: ModuleType,
    *,
    system_prompt_override: str,
    context_text: str | None = None,
):
    original_builder = getattr(factory_module, "build_system_prompt")

    def _build_prompt() -> str:
        return build_subagent_system_prompt(
            system_prompt_override,
            context_text=context_text,
        )

    setattr(factory_module, "build_system_prompt", _build_prompt)
    try:
        yield
    finally:
        setattr(factory_module, "build_system_prompt", original_builder)
