import asyncio
import logging
import uuid

from infra.logging import init_logging
from runtime.engine import AgentEngine
from runtime.planner_engine import PlannerEngine


log = logging.getLogger("flow.cli")


def new_thread_id() -> str:
    """Match the web client's `t_${shortId()}` thread-ID shape."""
    return f"t_{uuid.uuid4().hex[:16]}"


async def main():
    init_logging()
    log.info("starting CLI mode")

    main_engine = AgentEngine()
    planner_engine = PlannerEngine()
    await main_engine.initialize()
    await planner_engine.initialize()

    print("DeepAgent CLI 已启动。请选择一次 Agent；之后直接输入问题，exit 退出。\n")
    try:
        while True:
            selected = input("Agent [main/planner]: ").strip().lower()
            if selected == "exit":
                return
            if selected in {"main", "planner"}:
                break
            print("请输入 main、planner 或 exit。")

        engine = main_engine if selected == "main" else planner_engine
        thread_id = new_thread_id()
        log.info("CLI session selected agent=%s thread_id=%s", selected, thread_id)
        while True:
            question = input("\nUser: ").strip()
            if question == "exit":
                break
            if not question:
                continue

            result = await engine.run(question, thread_id=thread_id)
            print(f"\nAssistant: {result}\n")
    finally:
        await planner_engine.shutdown()
        await main_engine.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
