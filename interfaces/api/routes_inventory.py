"""Rutas de control de inventario, histórico de movimientos y alertas tempranas (RF09, RNF08, HU05)."""

from fastapi import APIRouter, Depends
from core.skill_base.skill_registry import SKILL_REGISTRY
from core.database.models import User
from interfaces.api.dependencies import require_admin

router = APIRouter(prefix="/inventory", tags=["Inventario"])


@router.get("/status")
def get_inventory_status(current_user: User = Depends(require_admin)):
    """Muestra stock actual, stock mínimo y estado general de cada producto (RF09)."""
    db_skill = SKILL_REGISTRY["db_repository"]()
    return db_skill.run({"action": "get_inventory_status"})


@router.get("/alerts")
def get_inventory_alerts(current_user: User = Depends(require_admin)):
    """Consulta alertas de productos con stock bajo o agotados para anticipar quiebres (HU05)."""
    db_skill = SKILL_REGISTRY["db_repository"]()
    monitor_skill = SKILL_REGISTRY["stock_monitor"]()

    inv_res = db_skill.run({"action": "get_inventory_status"})
    products = inv_res.get("products", [])

    return monitor_skill.run({"products": products})


@router.get("/movements")
def get_inventory_movements(current_user: User = Depends(require_admin)):
    """Consulta el histórico auditable de entradas y salidas de inventario (RNF08)."""
    db_skill = SKILL_REGISTRY["db_repository"]()
    inv_res = db_skill.run({"action": "get_inventory_status"})
    return inv_res.get("recent_movements", [])
