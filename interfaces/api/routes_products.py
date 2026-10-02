"""Rutas de gestión y consulta de productos (RF03, RF04, RF05, HU02)."""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from core.skill_base.skill_registry import SKILL_REGISTRY
from core.database.models import User
from core.security.guardrails import BusinessValidationError
from interfaces.api.dependencies import get_current_user, require_admin

router = APIRouter(prefix="/products", tags=["Productos"])


class ProductCreateRequest(BaseModel):
    code: Optional[str] = None
    name: str = Field(..., min_length=2)
    category: str = Field(..., min_length=2)
    description: Optional[str] = ""
    price: float
    stock_actual: int = Field(0, ge=0)
    stock_minimo: int = Field(5, ge=0)


class ProductUpdateRequest(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    stock_minimo: Optional[int] = None


@router.get("")
def list_products(
    category: Optional[str] = Query(None, description="Filtrar por categoría"),
    search: Optional[str] = Query(None, description="Buscar por nombre o código"),
    current_user: User = Depends(get_current_user)
):
    """Consulta de productos con búsqueda y filtro de categoría. Accesible para Admin y Vendedor (RF05)."""
    db_skill = SKILL_REGISTRY["db_repository"]()
    filters = {"active_only": True}
    if category:
        filters["category"] = category
    if search:
        filters["search"] = search

    res = db_skill.run({"action": "get_products", "filters": filters})
    return res.get("products", [])


@router.post("", status_code=201)
def create_product(
    req: ProductCreateRequest,
    current_user: User = Depends(require_admin)  # Solo Administrador (HU02)
):
    """Creación de un nuevo producto con categoría, precio y stock inicial (Solo Administrador, HU02)."""
    db_skill = SKILL_REGISTRY["db_repository"]()
    try:
        res = db_skill.run({
            "action": "create_product",
            "data": req.model_dump(),
            "user_id": current_user.id
        })
        return res.get("product")
    except BusinessValidationError as bve:
        raise HTTPException(status_code=400, detail=str(bve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creando producto: {str(e)}")


@router.put("/{product_id}")
def update_product(
    product_id: int,
    req: ProductUpdateRequest,
    current_user: User = Depends(require_admin)
):
    """Edición de un producto existente (Solo Administrador, RF03)."""
    db_skill = SKILL_REGISTRY["db_repository"]()
    try:
        res = db_skill.run({
            "action": "update_product",
            "product_id": product_id,
            "data": {k: v for k, v in req.model_dump().items() if v is not None}
        })
        if not res.get("product"):
            raise HTTPException(status_code=404, detail="Producto no encontrado.")
        return res.get("product")
    except BusinessValidationError as bve:
        raise HTTPException(status_code=400, detail=str(bve))


@router.delete("/{product_id}")
def deactivate_product(
    product_id: int,
    current_user: User = Depends(require_admin)
):
    """Desactivación lógica de un producto (Solo Administrador, RF03)."""
    db_skill = SKILL_REGISTRY["db_repository"]()
    res = db_skill.run({"action": "deactivate_product", "product_id": product_id})
    if not res.get("success"):
        raise HTTPException(status_code=404, detail="Producto no encontrado o ya inactivo.")
    return {"status": "success", "message": "Producto desactivado correctamente."}
