import os

from deepagents import create_deep_agent
from deepagents.backends import CompositeBackend, StoreBackend
from langchain_openai import ChatOpenAI

from tools import ToolSpec
from tools.core.registry import registry
from infra.config_loader import get_settings
from .prompts import build_system_prompt
from .middleware import install_registry_hooks

from runtime.workspace_manager import WorkspaceManager
from deepagents.backends.filesystem import FilesystemBackend

from langgraph.checkpoint.memory import MemorySaver
from langgraph.store.memory import InMemoryStore

from .tools import exec_shell


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
    def create_agent():

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
            max_retries=5,
            model_kwargs={
                "parallel_tool_calls": True,
            },
        )

        # -----------------------------
        # 加载工具
        # -----------------------------

        spec = ToolSpec(
            name="shell.exec_shell",
            description="执行终端命令",
            func=exec_shell,
            args_schema=exec_shell.args_schema  # @tool 装饰器会自动生成
        )
        registry.register(spec, exec_shell)

        tools = [
            exec_shell
        ]

        install_registry_hooks(registry)

        # 构建工具能力说明
        tool_prompt = AgentFactory.build_tool_prompt()

        # 把工具能力注入 system prompt
        system_prompt = build_system_prompt()

        # -----------------------------
        # 创建 DeepAgent
        # -----------------------------

        workspace = WorkspaceManager()
        workspace.ensure_workspace()

        #创建带有长期记忆的综合性backend
        # backend = FilesystemBackend(
        #     root_dir=workspace.get_root(),
        #     virtual_mode=True
        # )

        store = InMemoryStore()

        def make_backend(runtime):
            return CompositeBackend(
                default=FilesystemBackend(
                    root_dir=workspace.get_root(),
                    virtual_mode=True
                ),
                routes={
                    "/memories/": StoreBackend(runtime)
                }
            )

        memory = MemorySaver()

        agent = create_deep_agent(
            model=llm,
            tools=tools,
            system_prompt=system_prompt,
            backend=make_backend,
            store = store,
            checkpointer=memory,
            skills = ["/skills/"],
            interrupt_on = {
                "write_file": False,
                "read_file": False,
                "edit_file": True,
            },
            debug = False,
        )

        return agent