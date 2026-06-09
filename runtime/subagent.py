from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from types import ModuleType
from agents.prompts import SUMMARY_PROMPT
import threading
import uuid


@dataclass(frozen=True)
class SubagentContext:
    parent_thread_id: str
    user_id: str
    request_id: str | None = None
    fork_reason: str | None = None
    context_text: str | None = None


CONVERSATION_SUMMARY_TASK = "conversation_summary"
_PROMPT_OVERRIDE_LOCK = threading.RLock()


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


def is_conversation_summary_request(message: str) -> bool:
    if not message:
        return False

    normalized = "".join(str(message).strip().lower().split())
    if not normalized:
        return False

    explicit_phrases = (
        "总结对话",
        "总结一下对话",
        "总结这段对话",
        "总结当前对话",
        "总结一下当前对话",
        "概括对话",
        "概括一下对话",
        "概括当前对话",
        "概括这段对话",
        "summarizethisconversation",
        "summarizetheconversation",
        "conversationsummary",
    )
    if any(phrase in normalized for phrase in explicit_phrases):
        return True

    wants_summary = "总结" in normalized or "概括" in normalized or "summary" in normalized
    refers_conversation = "对话" in normalized or "会话" in normalized or "conversation" in normalized
    return wants_summary and refers_conversation


def build_conversation_summary_system_prompt() -> str:
    return SUMMARY_PROMPT.strip()


@contextmanager
def override_factory_prompt(
    factory_module: ModuleType,
    *,
    system_prompt_override: str,
    context_text: str | None = None,
):
    with _PROMPT_OVERRIDE_LOCK:
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
