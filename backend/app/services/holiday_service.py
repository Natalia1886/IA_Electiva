from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.holiday import ReligiousHoliday
from app.models.product import Product
from app.schemas.holiday import HolidayCreate, HolidayOut, HolidayUpdate
from app.services.ai.holiday_engine import VARIABLE_DATE_CODES


def _has_occurrence_source(holiday: ReligiousHoliday | dict) -> bool:
    def _get(key):
        return holiday.get(key) if isinstance(holiday, dict) else getattr(holiday, key)

    day, month = _get("day"), _get("month")
    if day is not None and month is not None:
        return True
    if _get("variable_date_code") in VARIABLE_DATE_CODES:
        return True
    return _get("start_date") is not None


def _validate_dates(holiday: ReligiousHoliday | dict) -> None:
    def _get(key):
        return holiday.get(key) if isinstance(holiday, dict) else getattr(holiday, key)

    start, end = _get("start_date"), _get("end_date")
    if start is not None and end is not None and end < start:
        raise ValueError("La fecha de fin debe ser posterior o igual a la fecha de inicio")


async def _resolve_products(db: AsyncSession, product_ids: list[int]) -> list[Product]:
    if not product_ids:
        return []
    result = await db.execute(select(Product).where(Product.id.in_(product_ids)))
    products = result.scalars().all()
    found = {p.id for p in products}
    missing = [pid for pid in product_ids if pid not in found]
    if missing:
        raise ValueError(f"Producto(s) no encontrado(s): {missing}")
    return list(products)


def _serialize(holiday: ReligiousHoliday) -> HolidayOut:
    return HolidayOut(
        id=holiday.id,
        name=holiday.name,
        day=holiday.day,
        month=holiday.month,
        variable_date_code=holiday.variable_date_code,
        start_date=holiday.start_date,
        end_date=holiday.end_date,
        expected_demand_factor=float(holiday.expected_demand_factor or 1.0),
        description=holiday.description,
        is_active=holiday.is_active,
        products=[
            {"id": p.id, "code": p.code, "name": p.name}
            for p in holiday.products
            if getattr(p, "is_active", True)
        ],
    )


async def _fetch_or_404(db: AsyncSession, holiday_id: int) -> ReligiousHoliday:
    result = await db.execute(
        select(ReligiousHoliday)
        .where(ReligiousHoliday.id == holiday_id)
        .options(selectinload(ReligiousHoliday.products))
    )
    holiday = result.scalar_one_or_none()
    if holiday is None:
        raise KeyError("Festividad no encontrada")
    return holiday


async def create_holiday(db: AsyncSession, payload: HolidayCreate) -> HolidayOut:
    data = payload.model_dump()
    product_ids = data.pop("product_ids", [])
    holiday = ReligiousHoliday(**data)

    if not _has_occurrence_source(holiday):
        raise ValueError(
            "Debe indicar una fecha fija (día/mes), una fecha variable o una fecha de inicio"
        )
    if holiday.day is not None and holiday.month is None:
        raise ValueError("Debe indicar el mes junto con el día")
    if holiday.month is not None and holiday.day is None:
        raise ValueError("Debe indicar el día junto con el mes")
    _validate_dates(holiday)

    try:
        holiday.products = await _resolve_products(db, product_ids)
        db.add(holiday)
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise ValueError("La festividad ya existe")
    await db.refresh(holiday, attribute_names=["products"])
    return _serialize(holiday)


async def update_holiday(db: AsyncSession, holiday_id: int, payload: HolidayUpdate) -> HolidayOut:
    holiday = await _fetch_or_404(db, holiday_id)
    data = payload.model_dump(exclude_unset=True)
    product_ids = data.pop("product_ids", None)

    for key, value in data.items():
        setattr(holiday, key, value)

    if not _has_occurrence_source(holiday):
        raise ValueError(
            "Debe indicar una fecha fija (día/mes), una fecha variable o una fecha de inicio"
        )
    _validate_dates(holiday)
    if product_ids is not None:
        holiday.products = await _resolve_products(db, product_ids)

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise ValueError("La festividad ya existe")
    await db.refresh(holiday, attribute_names=["products"])
    return _serialize(holiday)


async def deactivate_holiday(db: AsyncSession, holiday_id: int) -> None:
    holiday = await _fetch_or_404(db, holiday_id)
    holiday.is_active = False
    await db.commit()


def demand_factor_label(factor: float) -> str:
    if factor >= 2.0:
        return "alta"
    if factor > 1.3:
        return "media"
    return "baja"