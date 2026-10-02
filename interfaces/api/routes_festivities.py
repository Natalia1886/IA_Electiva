"""Rutas de gestión de festividades religiosas (RF10, HU06)."""

from typing import List, Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from core.skill_base.skill_registry import SKILL_REGISTRY
from core.database.models import User
from interfaces.api.dependencies import require_admin

router = APIRouter(prefix="/festivities", tags=["Festividades Religiosas"])


class FestivityCreateRequest(BaseModel):
    name: str = Field(..., min_length=3, description="Nombre de la festividad, ej. Semana Santa")
    start_date: str = Field(..., description="Fecha inicio YYYY-MM-DD")
    end_date: str = Field(..., description="Fecha fin YYYY-MM-DD")
    demand_factor: float = Field(1.5, gt=0, description="Factor multiplicador de demanda (ej. 1.8)")
    affected_categories: Optional[List[str]] = Field(default=[], description="Categorías impactadas")
    affected_products: Optional[List[str]] = Field(default=[], description="Productos impactados")
    description: Optional[str] = ""


@router.get("")
def list_festivities(current_user: User = Depends(require_admin)):
    """Consulta las festividades religiosas activas registradas en el sistema (RF10)."""
    db_skill = SKILL_REGISTRY["db_repository"]()
    res = db_skill.run({"action": "get_festivities"})
    return res.get("festivities", [])


@router.post("", status_code=201)
def create_festivity(
    req: FestivityCreateRequest,
    current_user: User = Depends(require_admin)  # Solo Administrador (HU06)
):
    """Registra una festividad religiosa con fechas, productos y factor de demanda (RF10, HU06)."""
    db_skill = SKILL_REGISTRY["db_repository"]()
    res = db_skill.run({
        "action": "create_festivity",
        "data": req.model_dump()
    })
    return res.get("festivity")
