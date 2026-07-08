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

    active_agent_name = type(engine.agent).__name__ if engine.agent is not None else "UnknownAgent"
    print(f"DeepAgent CLI 已启动，当前主链路 Agent: {active_agent_name} (exit退出)\n")

    while True:
        question = input("User: ")

        if question == "exit":
            break

        result = await engine.run(question)
        print(result)


if __name__ == "__main__":
    asyncio.run(main())
