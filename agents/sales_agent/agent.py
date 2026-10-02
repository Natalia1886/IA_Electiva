"""Agente Analista de Ventas y Cierre Diario (RF08).
Genera el balance del día con total recaudado, número de transacciones y productos con mayor movimiento.
"""

from typing import Dict, Any
from core.agent_base.base_agent import BaseAgent
from core.agent_base.agent_registry import register_agent
from core.skill_base.skill_registry import SKILL_REGISTRY
from core.memory.memory_manager import memory_manager
from core.observability.logger import get_logger

logger = get_logger("agent.sales")


@register_agent
class SalesAgent(BaseAgent):
    name = "sales_agent"

    def run(self, task: dict) -> dict:
        target_date = task.get("date")
        logger.info(f"Calculando balance diario de ventas para fecha: {target_date or 'hoy'}...")

        db_skill = SKILL_REGISTRY["db_repository"]()
        summary = db_skill.run({
            "action": "get_daily_summary",
            "target_date": target_date
        })

        # Cálculo de ticket promedio
        tx_count = summary.get("transaction_count", 0)
        total_amt = summary.get("total_sales_amount", 0.0)
        avg_ticket = round(total_amt / max(tx_count, 1), 2) if tx_count > 0 else 0.0

        result = {
            "date": summary.get("date"),
            "total_sales_amount": total_amt,
            "transaction_count": tx_count,
            "average_ticket": avg_ticket,
            "top_products": summary.get("top_products", []),
            "currency": "COP"
        }

        memory_manager.remember(f"sales_summary_{result['date']}", result)
        return result
