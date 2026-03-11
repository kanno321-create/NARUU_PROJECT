"""Tourism/medical package model."""

import enum
from typing import Optional

from sqlalchemy import ARRAY, Boolean, Enum, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.base import TimestampMixin


class PackageCategory(str, enum.Enum):
    MEDICAL = "medical"
    TOURISM = "tourism"
    COMBO = "combo"
    GOODS = "goods"


class Currency(str, enum.Enum):
    JPY = "JPY"
    KRW = "KRW"


class Package(Base, TimestampMixin):
    __tablename__ = "packages"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name_ja: Mapped[str] = mapped_column(String(200), nullable=False)
    name_ko: Mapped[str] = mapped_column(String(200), nullable=False)
    description_ja: Mapped[str | None] = mapped_column(Text)
    description_ko: Mapped[str | None] = mapped_column(Text)
    category: Mapped[PackageCategory] = mapped_column(
        Enum(PackageCategory, name="package_category"),
        nullable=False,
    )
    base_price: Mapped[Optional[float]] = mapped_column(Numeric(12, 2))
    currency: Mapped[Currency] = mapped_column(
        Enum(Currency, name="currency_type"),
        default=Currency.JPY,
        nullable=False,
    )
    duration_days: Mapped[int | None] = mapped_column(Integer)
    includes: Mapped[list[str] | None] = mapped_column(ARRAY(String(200)))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
