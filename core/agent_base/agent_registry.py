"""Registro central de agentes disponibles para el orquestador."""

AGENT_REGISTRY: dict = {}


def register_agent(agent_cls):
    AGENT_REGISTRY[agent_cls.name] = agent_cls
    return agent_cls
