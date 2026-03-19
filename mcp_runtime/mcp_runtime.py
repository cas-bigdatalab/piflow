import asyncio
import logging

from .client_manager import MCPClientManager
from .schema_cache import MCPSchemaCache
from .health_monitor import MCPHealthMonitor
from .reconnect_loop import MCPReconnectLoop
from .mcp_registry_loader import MCPToolLoader

from runtime.events import event_bus

log = logging.getLogger("flow.mcp.runtime")


class MCPRuntime:

    def __init__(self, mcp_config):

        self.config = mcp_config

        # manager
        self.manager = MCPClientManager(
            mcp_config.runtime
        )

        # schema cache
        self.cache = MCPSchemaCache()

        # loader
        self.loader = MCPToolLoader(
            self.manager,
            self.cache
        )

        # health monitor
        self.health = MCPHealthMonitor(
            self.manager,
            mcp_config.runtime
        )

        # reconnect loop
        self.reconnect = MCPReconnectLoop(
            self.manager,
            mcp_config.servers,
            self.loader,
            mcp_config.runtime
        )

        self._tasks = []

    async def start(self):

        log.info("runtime starting")
        event_bus.emit("runtime_started")

        tasks = []

        for server in self.config.servers:

            if not server.enabled:
                continue

            tasks.append(
                self.manager.connect(
                    server.name,
                    server.url
                )
            )

        await asyncio.gather(*tasks, return_exceptions=True)

        await self.loader.load_tools()

        self._tasks.append(
            asyncio.create_task(self.health.run())
        )

        self._tasks.append(
            asyncio.create_task(self.reconnect.run())
        )

        log.info("runtime started")

    async def shutdown(self):
        for t in self._tasks:
            t.cancel()

        event_bus.emit("runtime_shutdown")

        await self.manager.close_all()
