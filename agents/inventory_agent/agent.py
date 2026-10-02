"""Agente Auditor de Inventario y Alertas Tempranas (RF09, RF15, HU05).
Monitorea los niveles de existencias y notifica productos agotados o en riesgo de quiebre.
"""

from typing import Dict, Any
from core.agent_base.base_agent import BaseAgent
from core.agent_base.agent_registry import register_agent
from core.skill_base.skill_registry import SKILL_REGISTRY
from core.memory.memory_manager import memory_manager
from core.observability.logger import get_logger

logger = get_logger("agent.inventory")


@register_agent
class InventoryAgent(BaseAgent):
    name = "inventory_agent"

    def run(self, task: dict) -> dict:
        logger.info("Ejecutando auditoría de inventario y alertas tempranas...")

        db_skill = SKILL_REGISTRY["db_repository"]()
        monitor_skill = SKILL_REGISTRY["stock_monitor"]()

        # Consultar estado actual del inventario
        inv_data = db_skill.run({"action": "get_inventory_status"})
        products = inv_data.get("products", [])
        movements = inv_data.get("recent_movements", [])

        # Evaluar umbrales de alerta
        monitor_res = monitor_skill.run({"products": products})

        result = {
            "summary": {
                "total_products": len(products),
                "out_of_stock": monitor_res.get("out_of_stock_count", 0),
                "low_stock": monitor_res.get("low_stock_count", 0),
                "total_alerts": monitor_res.get("total_alerts", 0),
            },
            "alerts": monitor_res.get("alerts", []),
            "recent_movements": movements[:15]
        }

        memory_manager.remember("latest_inventory_alerts", result)
        return result
