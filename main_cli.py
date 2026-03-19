import asyncio
import logging

from infra.logging import init_logging
from runtime.engine import AgentEngine


log = logging.getLogger("flow.cli")


async def main():
    init_logging()
    log.info("starting CLI mode")

    engine = AgentEngine()
    await engine.initialize()

    print("DeepAgent CLI 已启动 (exit退出)\n")

    while True:
        question = input("User: ")

        if question == "exit":
            break

        result = await engine.run(question)
        print(result)


if __name__ == "__main__":
    asyncio.run(main())
