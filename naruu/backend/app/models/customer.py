"""Japanese patient/tourist customer model."""

from datetime import date
from typing import Optional

from sqlalchemy import ARRAY, Date, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.base import TimestampMixin


class Customer(Base, TimestampMixin):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name_ja: Mapped[str] = mapped_column(String(100), nullable=False)
    name_ko: Mapped[str | None] = mapped_column(String(100))
    email: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(30))
    line_user_id: Mapped[str | None] = mapped_column(String(100), unique=True, index=True)
    nationality: Mapped[str] = mapped_column(String(50), default="JP", nullable=False)
    visa_type: Mapped[str | None] = mapped_column(String(50))
    first_visit_date: Mapped[Optional[date]] = mapped_column(Date)
    preferred_language: Mapped[str] = mapped_column(String(10), default="ja", nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    tags: Mapped[list[str] | None] = mapped_column(ARRAY(String(50)))
