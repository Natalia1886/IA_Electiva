"""Rutas de registro de ventas y resumen diario (RF06, RF07, RF08, HU03)."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from core.skill_base.skill_registry import SKILL_REGISTRY
from core.database.models import User
from core.security.guardrails import BusinessValidationError
from interfaces.api.dependencies import get_current_user

router = APIRouter(prefix="/sales", tags=["Ventas"])


class SaleItemInput(BaseModel):
    product_id: int
    quantity: int = Field(..., gt=0, description="Cantidad vendida mayor a cero")


class SaleCreateRequest(BaseModel):
    items: List[SaleItemInput]
    payment_method: str = "EFECTIVO"
    notes: Optional[str] = ""


@router.post("", status_code=201)
def create_sale(
    req: SaleCreateRequest,
    current_user: User = Depends(get_current_user)  # Vendedor o Administrador (HU03)
):
    """Registra una venta con descuento automático atómico de stock e histórico auditable (RF06, RF07, RNF05, HU03)."""
    db_skill = SKILL_REGISTRY["db_repository"]()
    try:
        items_payload = [{"product_id": it.product_id, "quantity": it.quantity} for it in req.items]
        res = db_skill.run({
            "action": "register_sale",
            "sale_data": {
                "items": items_payload,
                "payment_method": req.payment_method,
                "notes": req.notes
            },
            "user_id": current_user.id
        })
        return res
    except BusinessValidationError as bve:
        raise HTTPException(status_code=400, detail=str(bve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en la transacción de venta: {str(e)}")


@router.get("/daily")
def get_daily_sales_summary(
    date: Optional[str] = Query(None, description="Fecha YYYY-MM-DD (por defecto hoy)"),
    current_user: User = Depends(get_current_user)
):
    """Consulta el resumen diario con ventas, total vendido y productos más vendidos (RF08)."""
    db_skill = SKILL_REGISTRY["db_repository"]()
    summary = db_skill.run({"action": "get_daily_summary", "target_date": date})
    return summary
