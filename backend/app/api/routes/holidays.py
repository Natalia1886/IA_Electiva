from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.deps import AdminUser, CurrentUser, DbDep
from app.models.holiday import ReligiousHoliday
from app.schemas.holiday import HolidayCreate, HolidayOut, HolidayUpdate
from app.services import holiday_service

router = APIRouter(prefix="/holidays", tags=["holidays"])


@router.get("", response_model=list[HolidayOut])
async def list_holidays(db: DbDep, user: CurrentUser):
    result = await db.execute(
        select(ReligiousHoliday)
        .options(selectinload(ReligiousHoliday.products))
        .order_by(ReligiousHoliday.month, ReligiousHoliday.day, ReligiousHoliday.name)
    )
    return [holiday_service._serialize(h) for h in result.scalars().all()]


@router.post("", response_model=HolidayOut, status_code=status.HTTP_201_CREATED)
async def create_holiday(payload: HolidayCreate, db: DbDep, user: AdminUser):
    try:
        return await holiday_service.create_holiday(db, payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{holiday_id}", response_model=HolidayOut)
async def update_holiday(holiday_id: int, payload: HolidayUpdate, db: DbDep, user: AdminUser):
    try:
        return await holiday_service.update_holiday(db, holiday_id, payload)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{holiday_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_holiday(holiday_id: int, db: DbDep, user: AdminUser):
    try:
        await holiday_service.deactivate_holiday(db, holiday_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))