"""Order/sales model."""

import enum
from typing import Optional

from sqlalchemy import Enum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.base import TimestampMixin


class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    PAID = "paid"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"


class Order(Base, TimestampMixin):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    customer_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("customers.id"), nullable=False, index=True
    )
    package_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("packages.id")
    )
    reservation_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("reservations.id")
    )
    total_amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="JPY", nullable=False)
    payment_status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus, name="payment_status"),
        default=PaymentStatus.PENDING,
        nullable=False,
    )
    payment_method: Mapped[str | None] = mapped_column(String(50))
    commission_rate: Mapped[Optional[float]] = mapped_column(Numeric(5, 2))
    commission_amount: Mapped[Optional[float]] = mapped_column(Numeric(12, 2))
    notes: Mapped[str | None] = mapped_column(Text)
