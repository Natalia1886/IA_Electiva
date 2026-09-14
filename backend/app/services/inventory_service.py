import logging

from datetime import date, datetime

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.exceptions import BadRequestError, NotFoundError
from app.core.stock_status import StockStatus, compute_stock_status
from app.models.product import Product
from app.models.stock import StockMovement

logger = logging.getLogger("milan")


def make_idempotency_ref(sale_id: int, product_id: int) -> str:
    return f"sale:{sale_id}:{product_id}"


async def adjust_stock(
    db,
    product: Product,
    quantity: int,
    movement_type: str,
    reason: str | None = None,
    reference_sale_id: int | None = None,
    user_id: int | None = None,
    unique_ref: str | None = None,
) -> StockMovement:
    """Apply a signed quantity (+in / -out) to a product's stock and log a movement.

    Use ``unique_ref`` to guard against double-application inside the same intent
    (e.g. re-recording a sale). The ref is encoded in the movement reason.
    """
    if unique_ref:
        existing = await db.execute(
            select(StockMovement).where(StockMovement.reason == unique_ref)
        )
        if existing.scalars().first() is not None:
            return None

    product.stock += quantity
    movement = StockMovement(
        product_id=product.id,
        quantity=quantity,
        movement_type=movement_type,
        reason=unique_ref or reason,
        reference_sale_id=reference_sale_id,
        user_id=user_id,
    )
    db.add(movement)
    return movement


async def list_movements(
    db,
    product_id: int | None = None,
    movement_type: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    limit: int = 200,
):
    stmt = (
        select(StockMovement)
        .options(selectinload(StockMovement.product))
        .order_by(StockMovement.created_at.desc())
        .limit(limit)
    )
    if product_id is not None:
        stmt = stmt.where(StockMovement.product_id == product_id)
    if movement_type is not None:
        stmt = stmt.where(StockMovement.movement_type == movement_type)
    if date_from is not None:
        stmt = stmt.where(StockMovement.created_at >= date_from)
    if date_to is not None:
        stmt = stmt.where(StockMovement.created_at < date_to)
    result = await db.execute(stmt)
    return result.scalars().unique().all()


async def register_movement(
    db,
    *,
    product: Product,
    quantity: int,
    movement_type: str,
    reason: str | None,
    user_id: int,
) -> StockMovement:
    """Record a manual inventory entry (received purchase, adjustment, return).

    The stock level is updated and a ``StockMovement`` row is written in the
    same transaction, exactly like a sale-triggered deduction.
    """
    signed = quantity if movement_type == "purchase" else -quantity
    if product.stock + signed < 0:
        raise BadRequestError("El movimiento dejaría stock negativo")

    movement = await adjust_stock(
        db,
        product,
        signed,
        movement_type,
        reason=reason,
        user_id=user_id,
    )
    await db.commit()
    await db.refresh(movement)
    return movement


def stock_status_for(stock: int, min_stock: int) -> StockStatus:
    """Pure status calculation exposed for handlers and consumers."""
    return compute_stock_status(stock, min_stock)


async def product_by_id_or_error(db, product_id: int) -> Product:
    product = await db.get(Product, product_id)
    if product is None or not product.is_active:
        raise NotFoundError("Producto no encontrado")
    return product


async def product_for_update(db, product_id: int) -> Product:
    """Fetch an active product with a FOR UPDATE row lock.

    Used inside a sale transaction so concurrent registrations serialize on the
    row: stock is read and decremented atomically, never checked then changed in
    two independent steps.
    """
    stmt = select(Product).where(Product.id == product_id).with_for_update()
    product = (await db.execute(stmt)).scalar_one_or_none()
    if product is None or not product.is_active:
        raise NotFoundError("Producto no encontrado")
    return product