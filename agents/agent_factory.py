import os

from deepagents import create_deep_agent
from deepagents.backends.filesystem import FilesystemBackend
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver
from deepagents.backends import CompositeBackend, StoreBackend
from langgraph.store.memory import InMemoryStore

from agents.prompts import DeepAgentPrompts
from agents.tools import exec_shell
from infra.config_loader import get_settings



root_dir = os.path.abspath(".")
backend = FilesystemBackend(
    root_dir=r"D:\hqr\projects\python\new-flow-deepagents\flow-deepagents\workspace",
    virtual_mode=True)

checkpointer = InMemorySaver()

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

model = ChatOpenAI(
    model=llm_cfg.model,
    temperature=llm_cfg.temperature,
    api_key=api_key,
    base_url=provider_cfg.base_url,
    max_retries=5,
    model_kwargs={
        "parallel_tool_calls": True,
    },
)

agent = create_deep_agent(
    model=model,
    system_prompt=DeepAgentPrompts.SYSTEM_PROMPT,
    backend=backend,
    skills=["/skills/"],
    tools=[exec_shell],
    interrupt_on={
        "write_file": False,
        "read_file": False,
        "edit_file": True,
    },
    checkpointer=checkpointer,
    debug=False,
)


store = InMemoryStore()

def make_backend(runtime):
    return CompositeBackend(
        default=FilesystemBackend(
            root_dir=r"D:\hqr\projects\python\new-flow-deepagents\flow-deepagents\workspace",
            virtual_mode=True
        ),
        routes={
            "/memories/": StoreBackend(runtime)
        }
    )

memory_agent = create_deep_agent(
    model=model,
    system_prompt=DeepAgentPrompts.SYSTEM_PROMPT,
    backend=make_backend,
    store=store,
    skills=["/skills/"],
    tools=[exec_shell],
    interrupt_on={
        "write_file": False,
        "read_file": False,
        "edit_file": True,
    },
    checkpointer=checkpointer,
    debug=False,
)