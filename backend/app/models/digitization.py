from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, Date, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class DigitizationRecord(Base):
    __tablename__ = "digitization_records"

    id: Mapped[int] = mapped_column(primary_key=True)
    original_filename: Mapped[str] = mapped_column(String(255))
    stored_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), default="pending", index=True
    )
    analyzer: Mapped[str | None] = mapped_column(String(50), nullable=True)
    record_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    raw_data: Mapped[list | None] = mapped_column(JSON, nullable=True)
    validated_data: Mapped[list | None] = mapped_column(JSON, nullable=True)
    correction_stats: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    uploaded_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    analyzed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)