import asyncio
import logging
from runtime.events import event_bus

log = logging.getLogger("flow.mcp.health")

class MCPHealthMonitor:

    def __init__(self, manager, runtime_config):

        self.manager = manager

        self.interval = runtime_config.health_check_interval

    async def check_once(self):

        dead = []

        for name, client in self.manager.list_clients():

            try:

                await asyncio.wait_for(
                    client.list_tools(),
                    timeout=3
                )

            except Exception:

                dead.append(name)

        for name in dead:

            log.warning("detected dead server=%s", name)

            event_bus.emit(
                "mcp_server_down",
                {"server": name}
            )

            await self.manager.remove(name)

    async def run(self):

        while True:

            await self.check_once()

            await asyncio.sleep(self.interval)
