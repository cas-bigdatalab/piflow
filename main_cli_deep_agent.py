import asyncio
import logging
import uuid

from infra.logging import init_logging
from runtime.engine import AgentEngine
from deep_agent_main import agent

log = logging.getLogger("flow.cli")

async def main():
    init_logging()
    log.info("starting CLI mode")

    engine = AgentEngine(agent)
    await engine.initialize()

    print("DeepAgent CLI 已启动 (exit退出)\n")

    while True:
        question = input("User: ")

        if question == "exit":
            break

        session_id = "user-1"  # 固定（表示对话）
        task_id = str(uuid.uuid4())  # 每次新任务

        thread_id = f"{session_id}:{task_id}"

        result = await engine.run(question, thread_id)
        print(result)


if __name__ == "__main__":
    asyncio.run(main())