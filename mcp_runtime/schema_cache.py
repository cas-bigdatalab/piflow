# mcp_runtime/schema_cache.py

from typing import Dict, Any


class MCPSchemaCache:

    def __init__(self):
        self.cache: Dict[str, Any] = {}

    def get(self, server: str):

        return self.cache.get(server)

    def set(self, server: str, schema):

        self.cache[server] = schema

    def clear(self, server: str):

        self.cache.pop(server, None)