"""Rutas del Dashboard consolidado (RF15).
Muestra ventas del día, estado de inventario, alertas, productos más vendidos y recomendaciones según el rol.
"""

from fastapi import APIRouter, Depends
from core.database.models import User
from core.skill_base.skill_registry import SKILL_REGISTRY
from core.orchestrator.executor import Executor
from core.security.permissions import is_admin
from interfaces.api.dependencies import get_current_user

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])
executor = Executor()


@router.get("")
def get_dashboard_data(current_user: User = Depends(get_current_user)):
    """Retorna los datos consolidados del dashboard adaptados al rol del usuario (RF15)."""
    db_skill = SKILL_REGISTRY["db_repository"]()
    monitor_skill = SKILL_REGISTRY["stock_monitor"]()

    # 1. Resumen de ventas de hoy (RF08)
    sales_summary = db_skill.run({"action": "get_daily_summary"})

    # 2. Estado de inventario y alertas (RF09, HU05)
    inv_data = db_skill.run({"action": "get_inventory_status"})
    products = inv_data.get("products", [])
    alerts_data = monitor_skill.run({"products": products})

    dashboard = {
        "user": {
            "name": current_user.full_name,
            "role": current_user.role
        },
        "sales_today": sales_summary,
        "inventory_overview": {
            "total_products": len(products),
            "out_of_stock": alerts_data.get("out_of_stock_count", 0),
            "low_stock": alerts_data.get("low_stock_count", 0)
        },
        "top_moving_products": sales_summary.get("top_products", [])
    }

    # Si es Administrador, incluir recomendaciones de compra y alertas completas (RF14, RF15)
    if is_admin(current_user.role):
        dashboard["alerts"] = alerts_data.get("alerts", [])
        
        # Ejecutar recomendador IA
        rec_task = {"intent": "recommend_purchases", "horizon_days": 15, "window_days": 30}
        rec_result = executor.execute(rec_task)
        if rec_result.get("status") == "success":
            dashboard["recommendations"] = rec_result.get("result", {}).get("recommendations", [])
            dashboard["festivities_evaluated"] = rec_result.get("result", {}).get("festivities_evaluated", [])
        else:
            dashboard["recommendations"] = []
            dashboard["festivities_evaluated"] = []

    return dashboard
