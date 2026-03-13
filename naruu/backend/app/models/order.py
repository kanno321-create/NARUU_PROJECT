"""Order/sales model."""

import enum
from typing import Optional

from sqlalchemy import Enum, ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.base import TimestampMixin
from app.models.package import Currency


class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    PAID = "paid"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"


class Order(Base, TimestampMixin):
    __tablename__ = "orders"
    __table_args__ = (
        Index("ix_orders_created_at", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    customer_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    package_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("packages.id", ondelete="SET NULL"),
        index=True,
    )
    reservation_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("reservations.id", ondelete="SET NULL"),
        index=True,
    )
    total_amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    currency: Mapped[Currency] = mapped_column(
        Enum(Currency, name="currency_type", create_type=False),
        default=Currency.JPY,
        nullable=False,
    )
    payment_status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus, name="payment_status"),
        default=PaymentStatus.PENDING,
        nullable=False,
        index=True,
    )
    payment_method: Mapped[str | None] = mapped_column(String(50))
    commission_rate: Mapped[Optional[float]] = mapped_column(Numeric(5, 2))
    commission_amount: Mapped[Optional[float]] = mapped_column(Numeric(12, 2))
    notes: Mapped[str | None] = mapped_column(Text)
