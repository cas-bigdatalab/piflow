import logging

from tools.core.registry import registry
from tools.adapters.mcp_adapter import MCPAdapter

log = logging.getLogger("flow.mcp.loader")


class MCPToolLoader:

    def __init__(self, manager, schema_cache):

        self.manager = manager
        self.cache = schema_cache

    async def load_tools(self):

        for name, client in self.manager.list_clients():

            if self.cache.get(name):
                continue

            await self._load_server(name, client)

    async def reload_server(self, name):

        client = self.manager.get(name)

        if not client:
            return

        self.cache.clear(name)

        await self._load_server(name, client)

    async def _load_server(self, name, client):

        try:

            tools = await client.list_tools()

            registered = []

            for tool in tools:

                spec, func = MCPAdapter.to_toolspec_and_func(
                    name,
                    client,
                    tool
                )

                if not registry.has(spec.name):

                    registry.register(spec, func)

                    registered.append(spec.name)

            self.cache.set(name, True)

            log.info("tools loaded from server=%s", name)

            if registered:

                log.info(
                    "registered tools server=%s count=%s tools=%s",
                    name,
                    len(registered),
                    registered,
                )

            else:

                log.info("no new tools registered from server=%s", name)

        except Exception as e:

            log.error("tool load failed server=%s error=%s", name, e)
