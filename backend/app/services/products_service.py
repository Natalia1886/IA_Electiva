"""Product catalog service (business logic + persistence).

The API routes stay thin controllers: every query/mutation for the products
resource goes through this module against the Postgres database via the async
session. Domain errors surface as :class:`app.core.exceptions` so the centralized
handlers shape the responses.
"""
from __future__ import annotations

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import BadRequestError, NotFoundError
from app.models.holiday import ReligiousHoliday
from app.models.product import Product, ProductCategory
from app.schemas.product import ProductCreate, ProductOut, ProductUpdate


def _load_options():
    return (selectinload(Product.category), selectinload(Product.holidays))


def _serialize(product: Product) -> ProductOut:
    out = ProductOut.model_validate(product)
    out.category_name = product.category.name if product.category else None
    out.low_stock = product.stock < product.min_stock
    out.holiday_ids = [h.id for h in product.holidays]
    return out


async def list_products(
    db: AsyncSession,
    *,
    category_id: int | None = None,
    search: str | None = None,
    low_stock: bool = False,
    include_inactive: bool = False,
    holiday_id: int | None = None,
) -> list[ProductOut]:
    stmt = select(Product).options(*_load_options()).order_by(Product.name)
    if not include_inactive:
        stmt = stmt.where(Product.is_active.is_(True))
    if category_id is not None:
        stmt = stmt.where(Product.category_id == category_id)
    if search:
        like = f"%{search}%"
        stmt = stmt.where(or_(Product.name.ilike(like), Product.code.ilike(like)))
    if low_stock:
        stmt = stmt.where(Product.stock < Product.min_stock)
    if holiday_id is not None:
        stmt = stmt.where(Product.holidays.any(ReligiousHoliday.id == holiday_id))

    products = (await db.execute(stmt)).scalars().unique().all()
    return [_serialize(p) for p in products]


async def get_product(db: AsyncSession, product_id: int, *, include_inactive: bool = False) -> ProductOut:
    stmt = select(Product).options(*_load_options()).where(Product.id == product_id)
    if not include_inactive:
        stmt = stmt.where(Product.is_active.is_(True))
    product = (await db.execute(stmt)).scalar_one_or_none()
    if product is None:
        raise NotFoundError(f"Producto con id {product_id} no encontrado")
    return _serialize(product)


async def create_product(db: AsyncSession, payload: ProductCreate) -> ProductOut:
    exists = await db.execute(select(Product).where(Product.code == payload.code))
    if exists.scalar_one_or_none():
        raise BadRequestError(f"El código '{payload.code}' ya existe")
    if payload.category_id is not None and await db.get(ProductCategory, payload.category_id) is None:
        raise BadRequestError("Categoría no encontrada")

    data = payload.model_dump()
    holiday_ids = data.pop("holiday_ids", [])
    product = Product(**data)
    if holiday_ids:
        holidays = (
            await db.execute(select(ReligiousHoliday).where(ReligiousHoliday.id.in_(holiday_ids)))
        ).scalars().all()
        product.holidays = holidays
    db.add(product)
    await db.commit()
    await db.refresh(product)
    return await get_product(db, product.id, include_inactive=True)


async def update_product(db: AsyncSession, product_id: int, payload: ProductUpdate) -> ProductOut:
    product = await _fetch_or_404(db, product_id)

    data = payload.model_dump(exclude_unset=True)
    holiday_ids = data.pop("holiday_ids", None)
    if "code" in data and data["code"] != product.code:
        exists = await db.execute(select(Product).where(Product.code == data["code"], Product.id != product_id))
        if exists.scalar_one_or_none():
            raise BadRequestError(f"El código '{data['code']}' ya existe")
    if holiday_ids is not None:
        holidays = (
            await db.execute(select(ReligiousHoliday).where(ReligiousHoliday.id.in_(holiday_ids)))
        ).scalars().all()
        product.holidays = holidays
    for key, value in data.items():
        setattr(product, key, value)
    await db.commit()
    await db.refresh(product)
    return _serialize(product)


async def deactivate_product(db: AsyncSession, product_id: int) -> None:
    """Soft delete: the record stays in the database, flagged inactive."""
    product = await _fetch_or_404(db, product_id)
    product.is_active = False
    await db.commit()


async def reactivate_product(db: AsyncSession, product_id: int) -> ProductOut:
    product = await _fetch_or_404(db, product_id)
    product.is_active = True
    await db.commit()
    await db.refresh(product)
    return _serialize(product)


async def _fetch_or_404(db: AsyncSession, product_id: int) -> Product:
    stmt = select(Product).options(*_load_options()).where(Product.id == product_id)
    product = (await db.execute(stmt)).scalar_one_or_none()
    if product is None:
        raise NotFoundError(f"Producto con id {product_id} no encontrado")
    return product