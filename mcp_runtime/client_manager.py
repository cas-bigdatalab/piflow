import asyncio
import logging
from typing import Dict, Optional
from fastmcp import Client

log = logging.getLogger("flow.mcp.client_manager")


class MCPClientManager:

    def __init__(self, runtime_config):

        self.clients: Dict[str, Client] = {}
        self.urls: Dict[str, str] = {}

        self.connect_locks: Dict[str, asyncio.Lock] = {}

        self.timeout = runtime_config.timeout
        self.retry_interval = runtime_config.retry_interval
        self.health_check_interval = runtime_config.health_check_interval

    async def connect(self, name: str, url: str) -> Optional[Client]:

        if name in self.clients:
            return self.clients[name]

        lock = self.connect_locks.setdefault(name, asyncio.Lock())

        async with lock:

            if name in self.clients:
                return self.clients[name]

            try:

                log.info("connecting server=%s", name)

                client = Client(url)

                await asyncio.wait_for(
                    client.__aenter__(),
                    timeout=self.timeout
                )

                self.clients[name] = client
                self.urls[name] = url

                log.info("connected server=%s", name)

                return client

            except Exception as e:

                log.error("connect failed server=%s error=%s", name, e)

                return None

    def get(self, name: str) -> Optional[Client]:
        return self.clients.get(name)

    def list_clients(self):
        return list(self.clients.items())

    async def remove(self, name: str):

        client = self.clients.pop(name, None)

        if not client:
            return

        try:
            await client.__aexit__(None, None, None)
        except Exception:
            pass

        log.info("client removed server=%s", name)

    async def close_all(self):

        for name in list(self.clients.keys()):
            await self.remove(name)
