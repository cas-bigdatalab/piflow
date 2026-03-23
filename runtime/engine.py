import asyncio
import logging
import time

from agents.factory import AgentFactory
from infra.config_loader import get_settings
from infra.env_loader import load_dotenv_file
from infra.logging import init_logging
from mcp_runtime.mcp_runtime import MCPRuntime
from runtime.skill_loader import SkillLoader
from runtime.workspace_manager import WorkspaceManager
from runtime.policy import Policy
from tools.core.registry import registry


log = logging.getLogger("flow.engine")


class AgentEngine:

    def __init__(self):
        self.agent = None
        self.initialized = False
        self.settings = get_settings()
        self.mcp_runtime = MCPRuntime(self.settings.mcp)

    async def initialize(self):
        if self.initialized:
            return

        init_logging()
        log.info("initializing Agent Runtime")

        load_dotenv_file()

        self.skill_loader = SkillLoader()
        self.skill_loader.load()

        # await self.mcp_runtime.start()

        skills = self.skill_loader.skills
        log.info("skills loaded count=%s", len(skills))

        for skill in skills:
            log.info("skill loaded name=%s", skill["name"])

        policy = Policy(**self.settings.policy.model_dump())
        registry.set_policy(policy)

        self.agent = AgentFactory.create_agent(
            skills=self.skill_loader.skills
        )

        self.initialized = True
        log.info("Agent Runtime initialized")

    async def run(self, message: str, thread_id: str = "default"):
        start_total = time.time()
        registry.begin_request()

        config = {
            "configurable": {
                "thread_id": thread_id
            }
        }

        input_message = {
            "messages": [
                {
                    "role": "user",
                    "content": message
                }
            ]
        }

        workspace = WorkspaceManager()
        before_outputs = workspace.list_outputs()

        events = []

        start_stream = time.time()

        async for event in self.agent.astream(input_message, config=config):
            events.append(event)

        log.info("agent stream finished cost=%.2fs", time.time() - start_stream)

        new_files = workspace.detect_new_outputs(before_outputs)

        if new_files:
            events.append({
                "type": "artifact",
                "files": [f"/outputs/{f}" for f in new_files]
            })

        final_answer = ""
        token_usage = None

        for event in reversed(events):

            model = event.get("model")

            if not model:
                continue

            messages = model.get("messages", [])

            for msg in reversed(messages):

                msg_type = getattr(msg, "type", None)
                tool_calls = getattr(msg, "tool_calls", None)

                if msg_type == "ai" and not tool_calls:

                    final_answer = getattr(msg, "content", "")

                    # 读取 token usage
                    metadata = getattr(msg, "response_metadata", None)

                    if metadata:
                        token_usage = metadata.get("token_usage")

                    break

            if final_answer:
                break

        latency = time.time() - start_total

        log.info("request finished total_cost=%.2fs", latency)

        # 输出 token usage
        if token_usage:

            log.info(
                "llm_usage latency=%.2fs input_tokens=%s output_tokens=%s total_tokens=%s",
                latency,
                token_usage.get("prompt_tokens"),
                token_usage.get("completion_tokens"),
                token_usage.get("total_tokens"),
            )

        else:

            log.info(
                "llm_usage latency=%.2fs token_usage=unknown",
                latency
            )

        return final_answer

    async def stream(self, message: str, thread_id: str = "default"):
        registry.begin_request()

        config = {
            "configurable": {
                "thread_id": thread_id
            }
        }

        input_message = {
            "messages": [
                {
                    "role": "user",
                    "content": message
                }
            ]
        }

        async for event in self.agent.astream(input_message, config=config):
            yield event

    async def shutdown(self):

        log.info("shutting down Agent Runtime")

        await self.mcp_runtime.shutdown()

        log.info("shutdown complete")
