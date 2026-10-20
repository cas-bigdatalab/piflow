"""Local waiting notices; no assumptions about remote MCP execution progress."""
import asyncio
from contextlib import asynccontextmanager


class Waiting:
    def __init__(self, delay, phase):
        self.delay, self.phase = delay, phase
        self.stage = "prepare"

    @asynccontextmanager
    async def during(self, message):
        async def remind():
            await asyncio.sleep(self.delay)
            await self.phase(self.stage, message)

        notice = asyncio.create_task(remind())
        try:
            yield
        finally:
            notice.cancel()
            await asyncio.gather(notice, return_exceptions=True)
