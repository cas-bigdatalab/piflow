"""Register agent capabilities in the existing server; never start another service."""
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from pathlib import Path

from fastapi import APIRouter
from fastapi.routing import APIRoute


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


class ScientificRoute(APIRoute):
    def get_route_handler(self):
        handler = super().get_route_handler()

        async def checked(request):
            try:
                return await handler(request)
            except Exception as exc:
                from .forecast.feedback import http_error
                return http_error(exc)

        return checked


def install_scientific_agents(app, *, resources=project_resources, **components):
    """Call once during host app construction, before its lifespan starts.

    Each agent owns its chat URL; the original /chat routes remain untouched.
    Each scientific capability adds its own routes. No app, engine or user store is replaced.
    The private route factory container has no listener or separate host lifecycle.
    """
    from .forecast.api import PREFIX, create_app

    if getattr(app.state, "scientific_agents_installed", False):
        raise ValueError("科学智能体已注册，不能重复安装")
    app.state.scientific_agents_installed = True
    extension = create_app(legacy=app, host_resources=resources, manage_legacy=False, **components)
    router = APIRouter(route_class=ScientificRoute)
    for route in extension.router.routes:
        if (isinstance(route, APIRoute) and route.path.startswith(PREFIX + "/forecast/")
                and not route.path.startswith(PREFIX + "/forecast/agent/")):
            router.add_api_route(route.path, route.endpoint, methods=route.methods, name=route.name)
    app.include_router(router)
    from .unified.api import install_unified
    install_unified(app)
    original_lifespan = app.router.lifespan_context

    @asynccontextmanager
    async def lifespan(host):
        async with original_lifespan(host) as state:
            # Start after the original engine has loaded environment/configuration;
            # close agent jobs before the original database/engine resources close.
            async with extension.router.lifespan_context(extension):
                extension.state.session_services = {"forecast": extension.state.sessions}
                host.state.scientific_agents = extension.state
                try:
                    yield state
                finally:
                    del host.state.scientific_agents

    app.router.lifespan_context = lifespan
