from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class CategoryBase(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str | None = None


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    is_active: bool | None = None


class CategoryOut(CategoryBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool
    created_at: datetime


class HolidayOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    day: int | None = None
    month: int | None = None
    variable_date_code: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    expected_demand_factor: float = 1.0
    description: str | None = None
    is_active: bool = True


class HolidayCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    day: int = Field(ge=1, le=31)
    month: int = Field(ge=1, le=12)
    variable_date_code: str | None = None
    description: str | None = None


class ProductBase(BaseModel):
    code: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=1, max_length=150)
    description: str | None = None
    category_id: int | None = None
    price: float = Field(ge=0)
    cost: float | None = Field(default=None, ge=0)
    min_stock: int = Field(default=0, ge=0)
    holiday_ids: list[int] = Field(default_factory=list)


class ProductCreate(ProductBase):
    stock: int = Field(default=0, ge=0)


class ProductUpdate(BaseModel):
    code: str | None = None
    name: str | None = None
    description: str | None = None
    category_id: int | None = None
    price: float | None = Field(default=None, ge=0)
    cost: float | None = Field(default=None, ge=0)
    min_stock: int | None = Field(default=None, ge=0)
    stock: int | None = Field(default=None, ge=0)
    holiday_ids: list[int] | None = None
    is_active: bool | None = None


class ProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    description: str | None = None
    category_id: int | None = None
    category_name: str | None = None
    price: float
    cost: float | None = None
    stock: int
    min_stock: int
    is_active: bool
    holiday_ids: list[int] = []
    holidays: list[HolidayOut] = []
    low_stock: bool = False