"""Explicit startup selection; disabled implementations are never imported."""
from contextlib import AsyncExitStack, asynccontextmanager
from dataclasses import dataclass
from functools import partial
from importlib import import_module
from pathlib import Path
from typing import Callable

import yaml

from .paths import AGENTS_ROOT
from .agent_profiles import AgentProfile, DATASET_QA_PROFILE
from .pubchem.profile import PROFILE as PUBCHEM_PROFILE


@dataclass(frozen=True)
class AgentSpec:
    prepare: Callable
    adapter: str
    session_path: str | None
    session_table: str
    session_id_column: str
    profile: AgentProfile | None = None

    def adapter_class(self):
        module, name = self.adapter.split(":")
        adapter = getattr(import_module(module, package=__package__), name)
        return adapter.for_profile(self.profile) if self.profile is not None else adapter

    @classmethod
    def tool_agent(cls, profile):
        return cls(partial(prepare_tool_agent, agent_profile=profile),
            ".unified.adapters.dataset_qa:DatasetQAAdapter", None, profile.table("sessions"), "id", profile)


def prepare_forecast(host, resources, dataset_qa, components):
    from fastapi import APIRouter
    from fastapi.routing import APIRoute
    from .forecast.api import PREFIX, create_app
    from .forecast.feedback import http_error

    class ForecastRoute(APIRoute):
        def get_route_handler(self):
            handler = super().get_route_handler()

            async def checked(request):
                try:
                    return await handler(request)
                except Exception as exc:
                    return http_error(exc)

            return checked

    extension = create_app(legacy=host, host_resources=resources, manage_legacy=False,
        shared_store=lambda: host.state.scientific_agents.store, **components)
    router = APIRouter(route_class=ForecastRoute)
    for route in extension.router.routes:
        if (isinstance(route, APIRoute) and route.path.startswith(PREFIX + "/forecast/")
                and not route.path.startswith(PREFIX + "/forecast/agent/")):
            router.add_api_route(route.path, route.endpoint, methods=route.methods, name=route.name)
    host.include_router(router)

    @asynccontextmanager
    async def lifespan(state):
        async with extension.router.lifespan_context(extension):
            state.agent_states["forecast"] = extension.state
            state.session_services["forecast"] = extension.state.sessions
            state.deleters["forecast"] = extension.state.delete_host_session
            yield

    return lifespan


def prepare_dataset_qa(host, resources, dataset_qa, components):
    return prepare_tool_agent(host, resources, dataset_qa, components,
        agent_profile=DATASET_QA_PROFILE, supplied_service=dataset_qa)


def prepare_tool_agent(host, resources, dataset_qa, components, *, agent_profile, supplied_service=None):
    @asynccontextmanager
    async def lifespan(state):
        from .shared import QASessions

        service = supplied_service
        if service is None:
            import os
            from infra.config_loader import CONFIG_DIR
            from .dataset_qa.contracts import Server
            from .dataset_qa.mcp import MCPGateway
            from .dataset_qa.service import DatasetQA

            def local_mcp():
                if url := os.getenv("DATASET_QA_MCP_URL"):
                    return url
                from mcp_servers.corpus_mcp import mcp
                return mcp

            gateway = MCPGateway({"piflow-corpus": Server(local_mcp, "本应用挂载的MCP服务")},
                config_path=os.getenv("DATASET_QA_MCP_CONFIG", str(CONFIG_DIR / "mcp_servers.yaml")),
                agent_profile=agent_profile)
            service = DatasetQA(state.store.engine, gateway=gateway, agent_profile=agent_profile)
        async with AsyncExitStack() as stack:
            stack.push_async_callback(service.close)
            await service.start()
            sessions = QASessions(service)
            state.agent_states[agent_profile.agent_id] = service
            state.session_services[agent_profile.agent_id] = sessions
            state.deleters[agent_profile.agent_id] = sessions.delete
            yield

    return lifespan


AGENTS = {
    "forecast": AgentSpec(prepare_forecast, ".unified.adapters.forecast:ForecastAdapter",
        "/api/piflow/v1/forecast/sessions", "forecast_sessions", "thread_id"),
    "dataset_qa": AgentSpec(prepare_dataset_qa, ".unified.adapters.dataset_qa:DatasetQAAdapter",
        None, "dataset_qa_sessions", "id", DATASET_QA_PROFILE),
    "pubchem": AgentSpec.tool_agent(PUBCHEM_PROFILE),
}
DEFAULT_AGENTS = ("forecast", "dataset_qa")


def validate_enabled(value):
    if not isinstance(value, list) or any(not isinstance(name, str) for name in value):
        raise ValueError("enabled_agents 必须是智能体名称列表；全部停用请使用 []")
    unknown = set(value) - AGENTS.keys()
    if unknown:
        raise ValueError(f"未知科学智能体：{', '.join(sorted(unknown))}")
    if len(value) != len(set(value)):
        raise ValueError("enabled_agents 中的智能体不能重复")
    profiles = [(name, spec.profile) for name, spec in AGENTS.items() if getattr(spec, "profile", None) is not None]
    if any(name != profile.agent_id for name, profile in profiles):
        raise ValueError("智能体注册名称必须与配置身份一致")
    for field in ("storage_namespace", "session_prefix"):
        if len({getattr(profile, field) for _, profile in profiles}) != len(profiles):
            raise ValueError("智能体存储命名空间和会话前缀不能重复")
    return tuple(value)


def load_enabled(path=None):
    config = Path(path) if path is not None else AGENTS_ROOT / "configs" / "agents.yaml"
    try:
        data = yaml.safe_load(config.read_text(encoding="utf-8-sig"))
    except FileNotFoundError:
        if path is None:
            return DEFAULT_AGENTS
        raise ValueError(f"智能体加载配置不存在：{config}") from None
    except yaml.YAMLError as exc:
        raise ValueError(f"智能体加载配置格式不正确：{config}") from exc
    if not isinstance(data, dict) or set(data) != {"enabled_agents"}:
        raise ValueError("智能体加载配置必须且只能包含 enabled_agents")
    return validate_enabled(data["enabled_agents"])
