"""Enrutador de tareas a los agentes especializados correspondientes."""

from typing import Optional
from core.agent_base.agent_registry import AGENT_REGISTRY
from core.observability.logger import get_logger

logger = get_logger("orchestrator.router")

INTENT_AGENT_MAP = {
    "recommend_purchases": "purchase_advisor_agent",
    "purchase_advice": "purchase_advisor_agent",
    "recommendations": "purchase_advisor_agent",
    "stock_alerts": "inventory_agent",
    "inventory_audit": "inventory_agent",
    "daily_summary": "sales_agent",
    "sales_report": "sales_agent",
}


class Router:
    """Decide qué agente atiende una tarea entrante."""

    @staticmethod
    def resolve_agent_name(task: dict) -> Optional[str]:
        intent = task.get("intent", "").lower().strip()
        agent_name = task.get("target_agent") or INTENT_AGENT_MAP.get(intent)
        if not agent_name:
            logger.warning(f"No se encontró agente para el intent: '{intent}'")
            return None
        return agent_name

    @staticmethod
    def get_agent_instance(task: dict):
        agent_name = Router.resolve_agent_name(task)
        if not agent_name:
            return None
        agent_cls = AGENT_REGISTRY.get(agent_name)
        if not agent_cls:
            logger.error(f"El agente '{agent_name}' no se encuentra registrado en AGENT_REGISTRY")
            return None
        return agent_cls()
