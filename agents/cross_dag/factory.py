"""跨域规划用的 LLM 构造。"""

from __future__ import annotations

import os

from langchain_openai import ChatOpenAI

from infra.config_loader import get_settings
from infra.non_thinking import non_thinking_options


class CrossDagLLMFactory:
    @staticmethod
    def create_llm(*, temperature: float | None = None) -> ChatOpenAI:
        settings = get_settings()
        from runtime.cross_dag.config import get_cross_dc_config

        xdc = get_cross_dc_config()
        llm_cfg = settings.llm
        provider_name = llm_cfg.provider
        provider_cfg = settings.providers.get(provider_name)

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

        kwargs: dict = {
            "model": xdc.llm_model or llm_cfg.model,
            "temperature": 0.0 if temperature is None else temperature,
            "api_key": api_key,
            "base_url": provider_cfg.base_url,
            "max_retries": 2,
            "timeout": xdc.llm_timeout_seconds,
        }

        if xdc.llm_json_mode:
            kwargs["model_kwargs"] = {"response_format": {"type": "json_object"}}

        # Both agent entry points always request non-thinking execution, even
        # when an old cross_dag configuration still enables thinking.
        kwargs.update(non_thinking_options(provider=provider_name, model=kwargs["model"], base_url=provider_cfg.base_url))

        try:
            return ChatOpenAI(**kwargs)
        except TypeError:
            extra = kwargs.pop("extra_body", None)
            if extra:
                kwargs.setdefault("model_kwargs", {})["extra_body"] = extra
            return ChatOpenAI(**kwargs)
