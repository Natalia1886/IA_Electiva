"""Descompone tareas complejas del negocio religioso en subtareas delegables."""

from typing import Dict, Any, List


class Planner:
    """Planificador de flujos de trabajo basados en agentes y skills."""

    @staticmethod
    def create_plan(task: Dict[str, Any]) -> List[Dict[str, Any]]:
        intent = task.get("intent", "").lower().strip()

        if intent in ["recommend_purchases", "purchase_advice", "recommendations"]:
            return [
                {"step": 1, "skill": "db_repository", "action": "fetch_products_and_sales"},
                {"step": 2, "skill": "product_segmentation", "action": "segment_products"},
                {"step": 3, "skill": "demand_forecaster", "action": "calculate_reorder_amounts"},
                {"step": 4, "skill": "nl_explainer", "action": "generate_explanations"},
            ]

        elif intent in ["stock_alerts", "inventory_audit"]:
            return [
                {"step": 1, "skill": "db_repository", "action": "fetch_inventory"},
                {"step": 2, "skill": "stock_monitor", "action": "evaluate_thresholds"},
            ]

        elif intent in ["daily_summary", "sales_report"]:
            return [
                {"step": 1, "skill": "db_repository", "action": "fetch_daily_sales"},
                {"step": 2, "skill": "sales_analyzer", "action": "aggregate_metrics"},
            ]

        return [{"step": 1, "action": "direct_agent_execution"}]
