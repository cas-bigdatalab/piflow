"""Explicit agent registration. Conversations stay bound; no per-turn LLM routing."""
from typing import Protocol

from .contracts import TurnInput


class ConversationAgent(Protocol):
    agent_id: str
    def turn(self, request: TurnInput) -> dict: ...
    def state(self, user: str, thread: str) -> dict: ...
    def close(self) -> None: ...


class AgentDirectory:
    def __init__(self):
        self._agents: dict[str, ConversationAgent] = {}

    def register(self, agent: ConversationAgent):
        if agent.agent_id in self._agents:
            raise ValueError(f"智能体已经注册：{agent.agent_id}")
        self._agents[agent.agent_id] = agent

    def get(self, agent_id: str) -> ConversationAgent:
        if agent_id not in self._agents:
            raise ValueError("智能体未注册")
        return self._agents[agent_id]

    def list(self):
        return list(self._agents)

    def close(self):
        for agent in self._agents.values():
            agent.close()
