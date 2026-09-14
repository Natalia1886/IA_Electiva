from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class HolidayProductRef(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str


class HolidayCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    day: int | None = Field(default=None, ge=1, le=31)
    month: int | None = Field(default=None, ge=1, le=12)
    variable_date_code: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    expected_demand_factor: float = Field(default=1.0, ge=1)
    description: str | None = None
    is_active: bool = True
    product_ids: list[int] = Field(default_factory=list)


class HolidayUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    day: int | None = Field(default=None, ge=1, le=31)
    month: int | None = Field(default=None, ge=1, le=12)
    variable_date_code: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    expected_demand_factor: float | None = Field(default=None, ge=1)
    description: str | None = None
    is_active: bool | None = None
    product_ids: list[int] | None = None


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
    products: list[HolidayProductRef] = []