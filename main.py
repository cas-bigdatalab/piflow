import asyncio
import logging

from infra.logging import init_logging
from runtime.engine import AgentEngine


log = logging.getLogger("flow.main")


async def main():
    init_logging()
    log.info("starting demo main mode")

    engine = AgentEngine()

    try:
        await engine.initialize()

        print("\n==============================")
        print(" DeepAgent 执行任务")
        print("==============================\n")

        events = await engine.run(
            "帮我生成一份销售统计报表",
            thread_id="user-session-001"
        )

        for event in events:
            for node_name, output in event.items():
                print(f"\n[节点: {node_name}]")
                if isinstance(output, dict):
                    for k, v in output.items():
                        print(f"{k}: {v}")
                else:
                    print(output)

        print("\n==============================")
        print(" 任务完成")
        print("==============================\n")
    finally:
        await engine.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
