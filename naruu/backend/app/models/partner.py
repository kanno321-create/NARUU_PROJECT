"""Partner hospital/business model."""

import enum
from datetime import date
from typing import Optional

from sqlalchemy import Boolean, Date, Enum, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.base import TimestampMixin


class PartnerType(str, enum.Enum):
    HOSPITAL = "hospital"
    CLINIC = "clinic"
    RESTAURANT = "restaurant"
    HOTEL = "hotel"
    SHOP = "shop"


class Partner(Base, TimestampMixin):
    __tablename__ = "partners"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name_ko: Mapped[str] = mapped_column(String(200), nullable=False)
    name_ja: Mapped[str | None] = mapped_column(String(200))
    type: Mapped[PartnerType] = mapped_column(
        Enum(PartnerType, name="partner_type"),
        nullable=False,
    )
    address: Mapped[str | None] = mapped_column(String(500))
    contact_person: Mapped[str | None] = mapped_column(String(100))
    phone: Mapped[str | None] = mapped_column(String(30))
    commission_rate: Mapped[Optional[float]] = mapped_column(Numeric(5, 2))
    contract_start: Mapped[Optional[date]] = mapped_column(Date)
    contract_end: Mapped[Optional[date]] = mapped_column(Date)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
