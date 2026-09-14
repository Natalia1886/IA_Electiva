from datetime import date

from pydantic import BaseModel

from app.schemas.inventory import InventoryItem, LowStockAlert


class DashboardOut(BaseModel):
    today: date
    today_sales_value: float
    today_transactions: int
    today_units: int
    week_trend: list[dict] = []
    low_stock_products: list[LowStockAlert] = []
    total_products: int
    total_stock_value: float
    top_products_30d: list[dict] = []


class HolidayUpcoming(BaseModel):
    id: int
    name: str
    date: date
    days_until: int


class RecommendationItem(BaseModel):
    product_id: int
    code: str
    name: str
    current_stock: int
    min_stock: int
    sold_last_30_days: int
    upcoming_holiday: str | None = None
    segment: str | None = None
    estimated_demand: float
    suggested_quantity: int
    reason: str | None = None
    rationale: str


class RecommendationOut(BaseModel):
    generated_for: date
    source: str
    items: list[RecommendationItem]
    summary: str | None = None