from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.product import ProductOut

PaymentMethod = Literal["cash", "card", "transfer"]


class SaleItemIn(BaseModel):
    product_id: int
    quantity: int = Field(ge=1)
    unit_price: float | None = Field(default=None, ge=0)


class SaleCreate(BaseModel):
    sale_date: date
    items: list[SaleItemIn] = Field(min_length=1)
    note: str | None = None
    payment_method: PaymentMethod = "cash"
    digitization_id: int | None = None


class SaleItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    product_name: str | None = None
    product_code: str | None = None
    quantity: int
    unit_price: float
    subtotal: float


class SaleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sale_number: str | None = None
    sale_date: date
    total: float
    status: str
    source: str
    payment_method: str
    salesperson_id: int | None = None
    salesperson_name: str | None = None
    digitization_id: int | None = None
    created_at: datetime
    items: list[SaleItemOut] = []
    item_count: int = 0


class TopProduct(BaseModel):
    product_id: int
    code: str
    name: str
    units_sold: int
    total_value: float


class DailyItem(BaseModel):
    product_id: int
    code: str
    name: str
    units_sold: int
    total_value: float


class DailySummary(BaseModel):
    date: date
    total_value: float
    transaction_count: int
    units_sold: int
    products_count: int
    items: list[DailyItem] = []
    top_products: list[TopProduct] = []


class SalesFilter(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    date_from: date | None = None
    date_to: date | None = None
    salesperson_id: int | None = None
    source: str | None = None