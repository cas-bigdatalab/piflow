import asyncio
from runtime.events import event_bus

class MCPReconnectLoop:

    def __init__(self, manager, servers, loader, runtime_config):

        self.manager = manager
        self.servers = servers
        self.loader = loader

        # 重连间隔
        self.interval = runtime_config.retry_interval

    async def run(self):

        while True:

            for server in self.servers:

                if not server.enabled:
                    continue

                if self.manager.get(server.name):
                    continue

                client = await self.manager.connect(
                    server.name,
                    server.url
                )

                if client:
                    await self.loader.reload_server(server.name)

                event_bus.emit(
                    "mcp_reconnected",
                    {"server": server.name}
                )

            await asyncio.sleep(self.interval)