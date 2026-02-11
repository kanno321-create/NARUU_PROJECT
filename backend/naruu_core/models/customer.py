"""고객(Customer), 예약(Booking), 상호작용(Interaction) 모델."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from naruu_core.models.base import NaruuBase, TimestampMixin


class Customer(NaruuBase, TimestampMixin):
    """NARUU 고객 — LINE 유저와 1:1 매핑."""

    __tablename__ = "customers"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    line_user_id: Mapped[str | None] = mapped_column(
        String(64), unique=True, index=True, nullable=True, default=None,
    )
    display_name: Mapped[str] = mapped_column(String(200), default="")
    language: Mapped[str] = mapped_column(String(5), default="ja")  # ja, ko, en
    phone: Mapped[str] = mapped_column(String(30), default="")
    email: Mapped[str] = mapped_column(String(255), default="")
    status: Mapped[str] = mapped_column(
        String(20), default="active",
    )  # active, inactive, blocked
    notes: Mapped[str] = mapped_column(Text, default="")

    bookings: Mapped[list[Booking]] = relationship(
        back_populates="customer",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    interactions: Mapped[list[Interaction]] = relationship(
        back_populates="customer",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class Booking(NaruuBase, TimestampMixin):
    """예약 — 고객 → 거래처 서비스 예약."""

    __tablename__ = "bookings"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    customer_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("customers.id", ondelete="CASCADE"),
    )
    partner_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("partners.id", ondelete="SET NULL"), default="",
    )
    service_name: Mapped[str] = mapped_column(String(200), default="")
    status: Mapped[str] = mapped_column(
        String(20), default="inquiry",
    )  # inquiry → confirmed → completed → cancelled
    price_krw: Mapped[int] = mapped_column(default=0)
    commission_krw: Mapped[int] = mapped_column(default=0)
    scheduled_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True, default=None,
    )
    notes: Mapped[str] = mapped_column(Text, default="")

    customer: Mapped[Customer] = relationship(back_populates="bookings")


class Interaction(NaruuBase, TimestampMixin):
    """고객 상호작용 로그 — LINE 메시지, 전화, 웹 등."""

    __tablename__ = "interactions"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    customer_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("customers.id", ondelete="CASCADE"),
    )
    channel: Mapped[str] = mapped_column(String(20))  # line, web, phone
    direction: Mapped[str] = mapped_column(String(10))  # inbound, outbound
    content: Mapped[str] = mapped_column(Text, default="")
    metadata_json: Mapped[str] = mapped_column(Text, default="{}")

    customer: Mapped[Customer] = relationship(back_populates="interactions")
