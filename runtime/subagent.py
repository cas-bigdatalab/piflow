from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
import logging
from types import ModuleType

from agents.prompts import SUMMARY_PROMPT
import threading
import uuid

log = logging.getLogger("flow.subagent")


@dataclass(frozen=True)
class SubagentContext:
    parent_thread_id: str
    user_id: str
    request_id: str | None = None
    fork_reason: str | None = None
    context_text: str | None = None


CONVERSATION_SUMMARY_TASK = "conversation_summary"
_PROMPT_OVERRIDE_LOCK = threading.RLock()
SUMMARY_ROUTE_MARKER = "__ROUTE_TO_CONVERSATION_SUMMARY__"
SUMMARY_ROUTE_PROMPT_BLOCK = """
## 总结路由规则

- 如果用户需要处理一系列数据处理或清洗任务，除非用户直接说明，始终应该在用户指定的这次任务结束时输出标记。
- 如果上述场景命中了skill 列表内类似的功能时，优先输出这个标记。
- 命中上述场景时，只输出该标记：`__ROUTE_TO_CONVERSATION_SUMMARY__`
- 除这个标记外不要输出任何解释、前后缀、JSON、Markdown 或其它文字。
- 如果用户只是在询问总结功能、触发方式、工作原理，或表达仍然含糊，也继续按正常主流程响应，不要输出该标记。
""".strip()


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


def build_summary_route_prompt_block() -> str:
    return SUMMARY_ROUTE_PROMPT_BLOCK


def is_summary_route_marker(message: str | None) -> bool:
    if message is None:
        return False
    return str(message).strip() == SUMMARY_ROUTE_MARKER


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

        def _build_prompt(*args, **kwargs) -> str:
            return build_subagent_system_prompt(
                system_prompt_override,
                context_text=context_text,
            )

        setattr(factory_module, "build_system_prompt", _build_prompt)
        try:
            yield
        finally:
            setattr(factory_module, "build_system_prompt", original_builder)
