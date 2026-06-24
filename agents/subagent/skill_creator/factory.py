from contextlib import contextmanager
import threading
import uuid

import agents.factory as factory_module

from .prompt import build_skill_creator_system_prompt

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


@contextmanager
def override_factory_prompt(
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


def build_transient_thread_id(prefix: str = "tmp") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class SkillCreatorAgentFactory:
    @staticmethod
    def create_agent(
        *,
        system_prompt_override: str | None = None,
        context_text: str | None = None,
    ):
        with override_factory_prompt(
            system_prompt_override=system_prompt_override or build_skill_creator_system_prompt(),
            context_text=context_text,
        ):
            return factory_module.AgentFactory.create_agent()
