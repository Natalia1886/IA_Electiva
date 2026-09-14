from datetime import date

from fastapi import APIRouter

from app.api.deps import AdminUser, AnyUser, DbDep
from app.schemas.reports import DashboardOut
from app.schemas.sale import DailySummary
from app.services import daily_summary_service

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/dashboard", response_model=DashboardOut)
async def dashboard(db: DbDep, user: AdminUser):
    data = await daily_summary_service.get_dashboard(db)
    return data


@router.get("/daily/{target_date}", response_model=DailySummary)
async def daily_report(target_date: date, db: DbDep, user: AdminUser):
    return await daily_summary_service.daily_summary(db, target_date)