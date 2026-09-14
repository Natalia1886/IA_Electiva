from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.exceptions import BadRequestError
from app.models.digitization import DigitizationRecord
from app.models.product import Product
from app.models.sale import Sale, SaleItem
from app.models.stock import StockMovement
from app.services import inventory_service
from app.services.ai import digitizer


async def create_sale(db, payload, user) -> Sale:
    """Register a sale as a single atomic unit.

    The sale header, its detail lines, the automatic stock deduction and the
    inventory movement log are all grouped in one transaction: either everything
    is committed together or, on any failure (e.g. missing stock), nothing is
    persisted and the partial state is rolled back.

    Concurrent safety: each product row is read with ``FOR UPDATE`` so two
    simultaneous sales cannot both pass a stock check and oversell.
    """
    if not payload.items:
        raise BadRequestError("Una venta debe incluir al menos un producto")

    record = None
    digitized = payload.digitization_id is not None
    if digitized:
        record = await db.get(DigitizationRecord, payload.digitization_id)
        if record is None:
            raise BadRequestError("Registro de digitalización no encontrado")
        if record.status == "imported":
            raise BadRequestError("Ese registro de digitalización ya fue importado")
        if not record.raw_data and record.status != "awaiting_review":
            raise BadRequestError("El registro de digitalización no está listo para confirmar")

    sale = Sale(
        sale_date=payload.sale_date,
        status="completed",
        source="digitized" if digitized else "manual",
        payment_method=payload.payment_method,
        salesperson_id=user.id,
        digitization_id=record.id if record else None,
        note=(
            f"Digitalizado desde '{record.original_filename}'"
            if record
            else payload.note
        ),
    )
    db.add(sale)
    await db.flush()

    products: dict[int, Product] = {}
    unit_prices: dict[int, float] = {}
    total: float = 0
    async with db.begin_nested():
        for item in payload.items:
            # Digitized rows describe HISTORICAL sales: the notebook records the
            # past; no current stock is consumed and no movement is logged.
            if digitized:
                stmt = select(Product).where(Product.id == item.product_id)
                product = (await db.execute(stmt)).scalar_one_or_none()
            else:
                product = await inventory_service.product_for_update(db, item.product_id)

            if product is None:
                raise BadRequestError(f"Producto {item.product_id} no encontrado")

            if not digitized:
                if product.stock < item.quantity:
                    raise BadRequestError(
                        f"Stock insuficiente para '{product.name}': disponible {product.stock}, "
                        f"solicitado {item.quantity}"
                    )

            unit_price = product.price
            if item.unit_price is not None:
                unit_price = item.unit_price  # reviewed price may differ from catalog

            products[product.id] = product
            unit_prices[product.id] = float(unit_price)
            subtotal = round(float(unit_price) * item.quantity, 2)
            total += subtotal
            db.add(
                SaleItem(
                    sale_id=sale.id,
                    product_id=product.id,
                    quantity=item.quantity,
                    unit_price=unit_price,
                    subtotal=subtotal,
                )
            )

            if not digitized:
                await inventory_service.adjust_stock(
                    db=db,
                    product=product,
                    quantity=-item.quantity,
                    movement_type="sale",
                    reason=f"Venta {sale.id}",
                    unique_ref=f"sale:{sale.id}:{product.id}",
                    reference_sale_id=sale.id,
                    user_id=user.id,
                )

    sale.total = total
    sale.sale_number = f"V{sale.id:06d}"
    await db.commit()

    if record:
        validated = digitizer.validated_entries_from_items(payload.sale_date, products, payload.items, unit_prices)
        record.validated_data = validated
        record.correction_stats = digitizer.compute_correction_stats(record.raw_data or [], validated)
        record.status = "imported"
        record.notes = (
            record.notes or ""
        ) + f" Confirmado: {len(payload.items)} líneas el {payload.sale_date.isoformat()}."
        await db.commit()

    await db.refresh(sale)
    return sale


async def fetch_sale(db, sale_id: int) -> Sale:
    stmt = (
        select(Sale)
        .options(selectinload(Sale.items).selectinload(SaleItem.product))
        .where(Sale.id == sale_id)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def list_sales(
    db,
    date_from: date | None = None,
    date_to: date | None = None,
    salesperson_id: int | None = None,
    source: str | None = None,
    limit: int = 200,
):
    stmt = (
        select(Sale)
        .options(selectinload(Sale.items).selectinload(SaleItem.product))
        .order_by(Sale.sale_date.desc(), Sale.id.desc())
        .limit(limit)
    )
    if date_from is not None:
        stmt = stmt.where(Sale.sale_date >= date_from)
    if date_to is not None:
        stmt = stmt.where(Sale.sale_date <= date_to)
    if salesperson_id is not None:
        stmt = stmt.where(Sale.salesperson_id == salesperson_id)
    if source is not None:
        stmt = stmt.where(Sale.source == source)
    result = await db.execute(stmt)
    return result.scalars().unique().all()