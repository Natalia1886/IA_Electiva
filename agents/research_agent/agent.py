"""Agente de investigación: usa web_search y document_generator."""

from core.agent_base.base_agent import BaseAgent


class ResearchAgent(BaseAgent):
    name = "research_agent"

    def run(self, task: dict) -> dict:
        raise NotImplementedError
