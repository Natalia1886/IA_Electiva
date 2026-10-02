"""Agente Inteligente Asesor de Compras (RF11, RF12, RF13, RF14, HU07).
Cruza stock actual, historial de ventas y festividades religiosas para recomendar
qué comprar, cuánto comprar y explicar el motivo en lenguaje natural.
"""

from typing import Dict, Any
from core.agent_base.base_agent import BaseAgent
from core.agent_base.agent_registry import register_agent
from core.skill_base.skill_registry import SKILL_REGISTRY
from core.memory.memory_manager import memory_manager
from core.observability.logger import get_logger

logger = get_logger("agent.purchase_advisor")


@register_agent
class PurchaseAdvisorAgent(BaseAgent):
    name = "purchase_advisor_agent"

    def run(self, task: dict) -> dict:
        logger.info("Iniciando análisis de compras con IA...")
        horizon_days = task.get("horizon_days", 15)
        window_days = task.get("window_days", 30)

        # 1. Obtener skills requeridas
        db_skill = SKILL_REGISTRY["db_repository"]()
        segmentation_skill = SKILL_REGISTRY["product_segmentation"]()
        forecaster_skill = SKILL_REGISTRY["demand_forecaster"]()
        explainer_skill = SKILL_REGISTRY["nl_explainer"]()

        # 2. Paso 1: Consultar base de datos
        products_res = db_skill.run({"action": "get_products", "filters": {"active_only": True}})
        products = products_res.get("products", [])

        sales_res = db_skill.run({"action": "get_sales_history", "days": window_days})
        sales_history = sales_res.get("history", [])

        fest_res = db_skill.run({"action": "get_festivities"})
        festivities = fest_res.get("festivities", [])

        # 3. Paso 2: Segmentar productos con ML (RF11)
        seg_res = segmentation_skill.run({
            "action": "segment",
            "products": products,
            "sales_history": sales_history,
            "festivities": festivities,
            "window_days": window_days
        })
        segmented_products = seg_res.get("segmented_products", [])

        # 4. Paso 3: Pronóstico y cantidades sugeridas (RF12)
        forecast_res = forecaster_skill.run({
            "segmented_products": segmented_products,
            "window_days": window_days,
            "horizon_days": horizon_days
        })
        raw_recommendations = forecast_res.get("recommendations", [])

        # 5. Paso 4: Generación de motivos en lenguaje natural (RF13, HU07)
        explained_res = explainer_skill.run({
            "recommendations": raw_recommendations,
            "festivities": festivities
        })
        final_recommendations = explained_res.get("explained_recommendations", [])

        # 6. Guardar en memoria para trazabilidad
        result_payload = {
            "total_recommendations": len(final_recommendations),
            "urgent_count": sum(1 for r in final_recommendations if r.get("priority") == "URGENTE"),
            "festivities_evaluated": [f["name"] for f in festivities],
            "recommendations": final_recommendations
        }
        memory_manager.remember("last_purchase_recommendations", result_payload, persistent=True)

        return result_payload
