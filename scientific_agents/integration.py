"""Register agent capabilities in the existing server; never start another service."""
from contextlib import AsyncExitStack, asynccontextmanager
from dataclasses import dataclass, field
import logging
from pathlib import Path

from .loading import AGENTS, load_enabled, validate_enabled
from .shared import BindingStore, SharedState, StoredSessions

log = logging.getLogger("flow.scientific_agents")


@dataclass(frozen=True)
class HostResources:
    root: Path
    database_url: str = field(repr=False)
    postgres_dsn: str | None = field(default=None, repr=False)


def project_resources() -> HostResources:
    """Reuse the host database and workspace settings, including escaped credentials."""
    from infra.config_loader import get_settings, resolve_workspace_root
    from psycopg.conninfo import make_conninfo
    from sqlalchemy import URL

    db = get_settings().database
    url = URL.create("postgresql+psycopg", username=db.user, password=db.password,
                     host=db.host, port=db.port, database=db.name)
    dsn = make_conninfo(host=db.host, port=db.port, user=db.user, password=db.password,
                       dbname=db.name, connect_timeout=10)
    return HostResources(resolve_workspace_root() / "scientific_agents" / "forecast",
                         url.render_as_string(hide_password=False), dsn)


def install_scientific_agents(app, *, resources=project_resources, dataset_qa=None,
        config_path=None, enabled_agents=None, **components):
    """Call once during host app construction, before its lifespan starts.

    Each agent owns its chat URL; the original /chat routes remain untouched.
    Each scientific capability adds its own routes. No app, engine or user store is replaced.
    The private route factory container has no listener or separate host lifecycle.
    """
    if getattr(app.state, "scientific_agents_installed", False):
        raise ValueError("科学智能体已注册，不能重复安装")
    enabled = load_enabled(config_path) if enabled_agents is None else validate_enabled(enabled_agents)
    resolved_resources = None
    lifespans = [(name, AGENTS[name].prepare(app, lambda: resolved_resources, dataset_qa, components))
        for name in enabled]
    app.state.scientific_agents_installed = True
    app.state.enabled_scientific_agents = enabled
    app.state.dataset_qa_enabled = "dataset_qa" in enabled
    from .unified.api import install_unified
    install_unified(app)
    original_lifespan = app.router.lifespan_context

    @asynccontextmanager
    async def lifespan(host):
        nonlocal resolved_resources
        async with original_lifespan(host) as state:
            # Start after the original engine has loaded environment/configuration;
            # close agent jobs before the original database/engine resources close.
            resolved_resources = resources() if callable(resources) else resources
            if resolved_resources is None:
                raise ValueError("科学智能体接入需要公共数据库资源")
            try:
                async with AsyncExitStack() as stack:
                    store = BindingStore(resolved_resources.database_url)
                    stack.callback(store.close)
                    shared = SharedState(store, enabled)
                    for name, spec in AGENTS.items():
                        if name not in enabled:
                            shared.session_services[name] = StoredSessions(store.engine,
                                spec.session_table, spec.session_id_column)
                    host.state.scientific_agents = shared
                    for name, start in lifespans:
                        await stack.enter_async_context(start(shared))
                        log.info("Scientific agent started: agent=%s", name)
                    log.info("Scientific agents ready: enabled=%s", list(enabled))
                    yield state
            finally:
                if hasattr(host.state, "scientific_agents"):
                    del host.state.scientific_agents
                resolved_resources = None

    app.router.lifespan_context = lifespan
