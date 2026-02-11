"""거래처(Partner) 및 서비스 모델."""

from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from naruu_core.models.base import NaruuBase, TimestampMixin


class Partner(NaruuBase, TimestampMixin):
    """NARUU 거래처 (의료/미용/관광 클리닉)."""

    __tablename__ = "partners"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    name_ja: Mapped[str] = mapped_column(String(200))
    name_ko: Mapped[str] = mapped_column(String(200), default="")
    category: Mapped[str] = mapped_column(String(20))  # medical, beauty, tourism
    address: Mapped[str] = mapped_column(String(500), default="")
    phone: Mapped[str] = mapped_column(String(30), default="")
    commission_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        default=Decimal("20.00"),
    )
    is_active: Mapped[bool] = mapped_column(default=True)
    notes: Mapped[str] = mapped_column(Text, default="")

    services: Mapped[list[PartnerService]] = relationship(
        back_populates="partner",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class PartnerService(NaruuBase, TimestampMixin):
    """거래처가 제공하는 개별 서비스."""

    __tablename__ = "partner_services"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    partner_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("partners.id", ondelete="CASCADE"),
    )
    name_ja: Mapped[str] = mapped_column(String(200))
    name_ko: Mapped[str] = mapped_column(String(200), default="")
    price_krw: Mapped[int] = mapped_column(default=0)
    duration_minutes: Mapped[int] = mapped_column(default=60)
    description: Mapped[str] = mapped_column(Text, default="")
    is_active: Mapped[bool] = mapped_column(default=True)

    partner: Mapped[Partner] = relationship(back_populates="services")
