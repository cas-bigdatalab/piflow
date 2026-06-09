from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
import logging
import os
from types import ModuleType

from agents.prompts import SUMMARY_PROMPT
from infra.config_loader import get_settings
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
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
SUMMARY_TRIGGER_ROUTER_PROMPT = """
你是一个对话路由判定器，只负责判断当前用户这句话是否应该触发“对当前会话做总结”的 summary subagent。

判定目标：
- 只有当用户的主要意图是要求系统总结、概括、回顾、整理、交接当前这段聊天/会话/上文讨论时，输出 YES。
- 如果用户是在要求总结文档、代码、日志、文章、文件、网页、需求、方案，输出 NO。
- 如果用户只是在提到“总结”这个词，但主要任务不是让系统总结当前会话，输出 NO。
- 如果表达含糊、无法确认、或只是询问总结功能本身，输出 NO。

输出要求：
- 只能输出 YES 或 NO
- 不要输出任何解释、标点、换行外内容
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


def _extract_text_content(content: object) -> str:
    if content is None:
        return ""

    if isinstance(content, str):
        return content

    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict):
                text = item.get("text") or item.get("content") or item.get("input")
                if text:
                    parts.append(str(text))
            elif item is not None:
                parts.append(str(item))
        return "".join(parts)

    if isinstance(content, dict):
        text = content.get("text") or content.get("content") or content.get("input")
        if text:
            return str(text)

    return str(content)


def _build_router_llm() -> ChatOpenAI:
    settings = get_settings()
    llm_cfg = settings.llm
    provider_name = llm_cfg.provider
    provider_cfg = getattr(settings.providers, provider_name, None)
    if provider_cfg is None:
        raise ValueError(f"Provider config not found: {provider_name}")

    api_key = None
    if provider_cfg.api_key_env:
        api_key = os.getenv(provider_cfg.api_key_env)
    if not api_key:
        api_key = os.getenv("LLM_API_KEY")
    if not api_key:
        raise ValueError(
            f"Missing API key for provider '{provider_name}'. "
            f"Set {provider_cfg.api_key_env} or LLM_API_KEY."
        )

    return ChatOpenAI(
        model=llm_cfg.model,
        temperature=0,
        api_key=api_key,
        base_url=provider_cfg.base_url,
        max_retries=2,
    )


async def is_conversation_summary_request(message: str) -> bool:
    if not message:
        return False

    message_text = str(message).strip()
    if not message_text:
        return False

    try:
        llm = _build_router_llm()
        response = await llm.ainvoke(
            [
                SystemMessage(content=SUMMARY_TRIGGER_ROUTER_PROMPT),
                HumanMessage(content=f"用户消息：{message_text}"),
            ]
        )
    except Exception:
        log.exception("summary subagent route classification failed")
        return False

    decision = _extract_text_content(getattr(response, "content", response)).strip().upper()
    return decision == "YES"


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
