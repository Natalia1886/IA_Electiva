from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select

from app.api.deps import DbDep, require_permission
from app.core.stock_status import compute_stock_status
from app.models.product import Product
from app.models.stock import StockMovement
from app.models.user import User
from app.schemas.inventory import InventoryItem, LowStockAlert, StockMovementIn, StockMovementOut, StockPosition
from app.services import daily_summary_service, inventory_service

router = APIRouter(prefix="/inventory", tags=["inventory"])


@router.get("", response_model=list[InventoryItem], dependencies=[Depends(require_permission("inventory:view:limited"))])
async def inventory_status(db: DbDep):
    """Current stock per product, with the live three-level status."""
    products = (
        (await db.execute(select(Product).where(Product.is_active.is_(True)).order_by(Product.name)))
        .scalars()
        .all()
    )
    return [
        InventoryItem(
            product_id=p.id,
            code=p.code,
            name=p.name,
            category_name=None,
            stock=p.stock,
            min_stock=p.min_stock,
            stock_status=compute_stock_status(p.stock, p.min_stock),
            low_stock=compute_stock_status(p.stock, p.min_stock) == "low",
            out_of_stock=p.stock == 0,
        )
        for p in products
    ]


@router.get("/alerts", response_model=list[LowStockAlert], dependencies=[Depends(require_permission("inventory:view:alerts"))])
async def stock_alerts(db: DbDep):
    """Products whose status is Low Stock or Out of Stock. Admin-only."""
    products = (
        (await db.execute(
            select(Product).where(Product.is_active.is_(True), Product.stock <= Product.min_stock).order_by(Product.stock)
        ))
        .scalars()
        .all()
    )
    return [
        LowStockAlert(
            product_id=p.id,
            code=p.code,
            name=p.name,
            category_name=None,
            stock=p.stock,
            min_stock=p.min_stock,
            stock_status=compute_stock_status(p.stock, p.min_stock),
            low_stock=compute_stock_status(p.stock, p.min_stock) == "low",
            out_of_stock=p.stock == 0,
            missing_units=max(0, p.min_stock - p.stock),
        )
        for p in products
    ]


@router.get("/position", response_model=StockPosition, dependencies=[Depends(require_permission("inventory:view:limited"))])
async def stock_position(db: DbDep):
    position = await daily_summary_service.inventory_stock_position(db)
    return position


@router.get("/movements", response_model=list[StockMovementOut], dependencies=[Depends(require_permission("inventory:view:history"))])
async def list_movements(
    db: DbDep,
    product_id: int | None = None,
    movement_type: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    limit: int = 200,
):
    """Stock-in / stock-out history, optionally filtered per product, type or date."""
    movements = await inventory_service.list_movements(
        db,
        product_id=product_id,
        movement_type=movement_type,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
    )
    products = {}
    product_ids = {m.product_id for m in movements}
    if product_ids:
        rows = (await db.execute(select(Product).where(Product.id.in_(product_ids)))).scalars().all()
        products = {p.id: p for p in rows}
    return [
        StockMovementOut(
            id=m.id,
            product_id=m.product_id,
            product_name=products[m.product_id].name if m.product_id in products else None,
            product_code=products[m.product_id].code if m.product_id in products else None,
            quantity=m.quantity,
            movement_type=m.movement_type,
            reason=m.reason,
            reference_sale_id=m.reference_sale_id,
            user_id=m.user_id,
            created_at=m.created_at,
        )
        for m in movements
    ]


@router.post("/movements", response_model=StockMovementOut, status_code=status.HTTP_201_CREATED)
async def create_movement(
    payload: StockMovementIn,
    db: DbDep,
    user: Annotated[User, Depends(require_permission("inventory:manage"))],
):
    """Register a manual entry (received purchase, adjustment, return). Admin-only."""
    product = await db.get(Product, payload.product_id)
    if product is None or not product.is_active:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    movement = await inventory_service.register_movement(
        db,
        product=product,
        quantity=payload.quantity,
        movement_type=payload.movement_type,
        reason=payload.reason,
        user_id=user.id,
    )
    return StockMovementOut(
        id=movement.id,
        product_id=movement.product_id,
        product_name=product.name,
        product_code=product.code,
        quantity=movement.quantity,
        movement_type=movement.movement_type,
        reason=movement.reason,
        reference_sale_id=movement.reference_sale_id,
        user_id=movement.user_id,
        created_at=movement.created_at,
    )