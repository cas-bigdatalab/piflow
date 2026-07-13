import asyncio
import logging

from infra.logging import init_logging
from runtime.engine import AgentEngine
from runtime.planner_engine import PlannerEngine


log = logging.getLogger("flow.cli")


async def main():
    init_logging()
    log.info("starting CLI mode")

    main_engine = AgentEngine()
    planner_engine = PlannerEngine()
    await main_engine.initialize()
    await planner_engine.initialize()

    print("DeepAgent CLI 已启动。输入 main 或 planner 选择 Agent；exit 退出。\n")
    try:
        while True:
            selected = input("Agent [main/planner]: ").strip().lower()
            if selected == "exit":
                break
            if selected not in {"main", "planner"}:
                print("请输入 main、planner 或 exit。")
                continue

            question = input("User: ")
            if question == "exit":
                break

            engine = main_engine if selected == "main" else planner_engine
            result = await engine.run(question)
            print(result)
    finally:
        await planner_engine.shutdown()
        await main_engine.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
