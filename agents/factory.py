import os

from deepagents import create_deep_agent
from langchain_openai import ChatOpenAI

from tools.core.registry import registry
from tools.adapters.deepagents_adapter import DeepAgentsAdapter
from infra.config_loader import get_settings
from .prompts import build_system_prompt
from .middleware import install_registry_hooks

from runtime.workspace_manager import WorkspaceManager
from deepagents.backends.filesystem import FilesystemBackend

from langgraph.checkpoint.memory import MemorySaver



class AgentFactory:

    # 生成 tool 能力描述
    @staticmethod
    def build_tool_prompt():

        records = registry.list_records()

        if not records:
            return "当前系统未注册任何工具。"

        lines = []

        for rec in records:

            spec = rec.spec

            # 工具名 + 描述
            lines.append(
                f"- {spec.name}: {spec.description}"
            )

        return "\n".join(lines)

    @staticmethod
    def create_agent(skills=None):

        settings = get_settings()

        llm_cfg = settings.llm
        provider_name = llm_cfg.provider

        provider_cfg = getattr(settings.providers, provider_name, None)

        if provider_cfg is None:
            raise ValueError(f"Provider config not found: {provider_name}")

        # -----------------------------
        # 读取 API Key
        # -----------------------------

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

        # -----------------------------
        # 创建 LLM
        # -----------------------------

        llm = ChatOpenAI(
            model=llm_cfg.model,
            temperature=llm_cfg.temperature,
            api_key=api_key,
            base_url=provider_cfg.base_url,
            max_retries=2,
            model_kwargs={
                "parallel_tool_calls": False
            }
        )

        # -----------------------------
        # 加载工具
        # -----------------------------

        tool_records = registry.list_records()

        tools = [
            DeepAgentsAdapter.to_deepagents_tool(rec.spec, registry)
            for rec in tool_records
        ]

        install_registry_hooks(registry)

        # 构建工具能力说明
        tool_prompt = AgentFactory.build_tool_prompt()

        # 把工具能力注入 system prompt
        # system_prompt = build_system_prompt(tool_prompt)
        system_prompt = build_system_prompt(skills)


        # -----------------------------
        # 创建 DeepAgent
        # -----------------------------

        workspace = WorkspaceManager()
        workspace.ensure_workspace()

        backend = FilesystemBackend(
            root_dir=workspace.get_root(),
            virtual_mode=True
        )

        memory = MemorySaver()

        agent = create_deep_agent(
            model=llm,
            tools=tools,
            system_prompt=system_prompt,
            backend=backend,
            checkpointer=memory
        )

        return agent