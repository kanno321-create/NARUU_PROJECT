"""Reservation/schedule model."""

import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.base import TimestampMixin


class ReservationStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ReservationType(str, enum.Enum):
    MEDICAL = "medical"
    TOURISM = "tourism"
    RESTAURANT = "restaurant"
    GOODS = "goods"


class Reservation(Base, TimestampMixin):
    __tablename__ = "reservations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    customer_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("customers.id"), nullable=False, index=True
    )
    package_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("packages.id")
    )
    partner_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("partners.id")
    )
    reservation_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    status: Mapped[ReservationStatus] = mapped_column(
        Enum(ReservationStatus, name="reservation_status"),
        default=ReservationStatus.PENDING,
        nullable=False,
    )
    type: Mapped[ReservationType] = mapped_column(
        Enum(ReservationType, name="reservation_type"),
        nullable=False,
    )
    notes_ja: Mapped[str | None] = mapped_column(Text)
    notes_ko: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id")
    )
