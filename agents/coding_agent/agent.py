"""Agente de código: usa code_executor."""

from core.agent_base.base_agent import BaseAgent


class CodingAgent(BaseAgent):
    name = "coding_agent"

    def run(self, task: dict) -> dict:
        raise NotImplementedError
