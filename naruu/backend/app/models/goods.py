"""Goods/merchandise model."""

import enum

from sqlalchemy import ARRAY, Boolean, Enum, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.base import TimestampMixin


class GoodsCategory(str, enum.Enum):
    BAG = "bag"
    ACCESSORY = "accessory"
    SOUVENIR = "souvenir"


class Goods(Base, TimestampMixin):
    __tablename__ = "goods"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name_ja: Mapped[str] = mapped_column(String(200), nullable=False)
    name_ko: Mapped[str] = mapped_column(String(200), nullable=False)
    description_ja: Mapped[str | None] = mapped_column(Text)
    description_ko: Mapped[str | None] = mapped_column(Text)
    category: Mapped[GoodsCategory] = mapped_column(
        Enum(GoodsCategory, name="goods_category"),
        nullable=False,
    )
    price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    stock_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    image_urls: Mapped[list[str] | None] = mapped_column(ARRAY(String(500)))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
