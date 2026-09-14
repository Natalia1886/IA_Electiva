from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.product import Product
    from app.models.user import User


class Sale(Base):
    __tablename__ = "sales"

    id: Mapped[int] = mapped_column(primary_key=True)
    sale_number: Mapped[str | None] = mapped_column(String(30), unique=True, nullable=True)
    sale_date: Mapped[date] = mapped_column(Date, index=True)
    total: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    status: Mapped[str] = mapped_column(String(20), default="completed", index=True)
    source: Mapped[str] = mapped_column(String(20), default="manual", index=True)
    payment_method: Mapped[str] = mapped_column(String(20), default="cash", index=True)
    salesperson_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    digitization_id: Mapped[int | None] = mapped_column(
        ForeignKey("digitization_records.id"), nullable=True
    )
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    items: Mapped[list["SaleItem"]] = relationship(
        back_populates="sale", cascade="all, delete-orphan", lazy="selectin"
    )


class SaleItem(Base):
    __tablename__ = "sale_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    sale_id: Mapped[int] = mapped_column(ForeignKey("sales.id", ondelete="CASCADE"), index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), index=True)
    quantity: Mapped[int] = mapped_column(Integer)
    unit_price: Mapped[float] = mapped_column(Numeric(12, 2))
    subtotal: Mapped[float] = mapped_column(Numeric(12, 2))

    sale: Mapped[Sale] = relationship(back_populates="items")
    product: Mapped["Product"] = relationship(lazy="selectin")