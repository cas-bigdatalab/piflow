"""Non-thinking request options, explicitly used by forecast and cross_dag only.

Service protocols take precedence over model-family defaults. These are request
switches, not instructions to hide reasoning text or silently change models.
"""
import logging
import re
from urllib.parse import urlsplit

log = logging.getLogger(__name__)


def _platform(provider: str, host: str) -> str:
    # Recognized endpoints take precedence over configuration aliases (e.g.
    # an OpenAI-compatible service registered under the name "openai").
    if host == "relayrouter.ai" or host.endswith(".relayrouter.ai"):
        return "relayrouter"
    if host == "openrouter.ai" or host.endswith(".openrouter.ai"):
        return "openrouter"
    if host.endswith(".aliyuncs.com") and (
        host.split(".", 1)[0].startswith("dashscope") or host.endswith(".maas.aliyuncs.com")
    ):
        return "dashscope"
    return provider


def non_thinking_options(*, provider: str, model: str, base_url: str) -> dict:
    """Return ChatOpenAI options without changing shared configuration."""
    provider = provider.strip().casefold()
    name = model.strip().casefold().rsplit("/", 1)[-1]
    host = (urlsplit(str(base_url)).hostname or "").casefold()
    platform = _platform(provider, host)

    # These model variants cannot disable reasoning. Do not disguise a low
    # reasoning budget or omitted reasoning text as non-thinking execution.
    if (name.startswith(("deepseek-r1", "qwq", "kimi-k2-thinking", "kimi-k2.7-code", "kimi-k3", "glm-5.3"))
            or (name.startswith("qwen") and re.search(r"(?:^|-)thinking(?:-|$)", name))):
        raise ValueError(f"模型 {model} 不支持关闭思考；预测和 cross_dag 请使用支持非思考模式的型号。")

    # Gateway protocols override the underlying model's native API protocol.
    if platform == "openrouter":
        return {"extra_body": {"reasoning": {"enabled": False}}}
    if platform == "dashscope":
        return {"extra_body": {"enable_thinking": False}}

    # Native switches, also used by transparent OpenAI-compatible relays.
    # https://api-docs.deepseek.com/guides/thinking_mode/
    # https://help.aliyun.com/zh/model-studio/deep-thinking
    # https://docs.bigmodel.cn/cn/guide/capabilities/thinking-mode
    # https://platform.kimi.ai/docs/guide/use-thinking-models
    if name.startswith("qwen"):
        # RelayRouter and direct Qwen endpoints use the same top-level flag
        # as DashScope; the SDK flattens this extra_body argument into JSON.
        return {"extra_body": {"enable_thinking": False}}
    if name.startswith(("deepseek", "glm-4.5", "glm-4.6", "glm-4.7", "glm-5", "kimi-k2.5", "kimi-k2.6")):
        return {"extra_body": {"thinking": {"type": "disabled"}}}

    # Preserve ordinary non-reasoning models without sending unsupported fields.
    if name.startswith(("gpt-3.5", "gpt-4", "moonshot-v1")):
        return {}
    log.warning("模型 %s 的关闭思考协议尚未适配，未发送关闭参数；请核对服务支持情况。", model)
    return {}
