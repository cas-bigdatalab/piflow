import os

from deepagents import create_deep_agent
from deepagents.backends import CompositeBackend, StoreBackend
from deepagents.backends.filesystem import FilesystemBackend
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.store.memory import InMemoryStore

from agents.subagent.skill_creator.prompt import build_skill_creator_route_prompt_block
from agents.tools import exec_shell
from infra.config_loader import get_settings
from runtime.workspace_manager import WorkspaceManager
from tools import ToolSpec
from tools.core.registry import registry
from agents.middleware import install_registry_hooks
from .prompt import build_skill_planner_system_prompt


class SkillPlannerAgentFactory:
    @staticmethod
    def _ensure_builtin_tools_registered() -> None:
        if registry.has("shell.exec_shell"):
            return

        spec = ToolSpec(
            name="shell.exec_shell",
            description="执行终端命令",
            func=exec_shell,
            args_schema=exec_shell.args_schema,
        )
        registry.register(spec, exec_shell)

    @staticmethod
    def create_agent():
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

        SkillPlannerAgentFactory._ensure_builtin_tools_registered()
        tools = [exec_shell]
        install_registry_hooks(registry)

        system_prompt = build_skill_planner_system_prompt(
            extra_sections=[build_skill_creator_route_prompt_block()]
        )

        workspace = WorkspaceManager()
        workspace.ensure_workspace()

        store = InMemoryStore()
        backend = CompositeBackend(
            default=FilesystemBackend(
                root_dir=workspace.get_root(),
                virtual_mode=True,
            ),
            routes={
                "/memories/": StoreBackend(
                    namespace=lambda ctx: (
                        ((getattr(getattr(ctx, "runtime", None), "context", None) or {}).get("user_id", "default_user")),
                    )
                )
            },
        )

        memory = MemorySaver()

        agent = create_deep_agent(
            model=llm,
            tools=tools,
            system_prompt=system_prompt,
            backend=backend,
            store=store,
            checkpointer=memory,
            skills=["skills/planner"],
            interrupt_on={
                "write_file": False,
                "read_file": False,
                "edit_file": False,
            },
            debug=False,
        )

        return agent
