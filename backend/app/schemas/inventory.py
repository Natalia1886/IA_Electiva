from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class StockMovementIn(BaseModel):
    product_id: int
    quantity: int = Field(gt=0)
    movement_type: str = Field(pattern="^(purchase|adjustment|return)$")
    reason: str | None = None


class StockMovementOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    product_name: str | None = None
    product_code: str | None = None
    quantity: int
    movement_type: str
    reason: str | None = None
    reference_sale_id: int | None = None
    user_id: int | None = None
    created_at: datetime


class InventoryItem(BaseModel):
    product_id: int
    code: str
    name: str
    category_name: str | None = None
    stock: int
    min_stock: int
    stock_status: str = "normal"
    low_stock: bool = False
    out_of_stock: bool = False


class LowStockAlert(InventoryItem):
    missing_units: int


class StockPosition(BaseModel):
    total_units: int
    total_products: int
    products_low: int
    stock_value: float
    low_stock: list[LowStockAlert]