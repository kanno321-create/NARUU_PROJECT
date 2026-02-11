"""관광 추천 모델."""

from __future__ import annotations

import uuid

from sqlalchemy import Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from naruu_core.models.base import NaruuBase, TimestampMixin


class Spot(NaruuBase, TimestampMixin):
    """관광 스팟 (클리닉, 관광지, 맛집 등).

    스코어링: preference_match + popularity + distance_penalty + budget_fit
    """

    __tablename__ = "spots"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4()),
    )
    name_ja: Mapped[str] = mapped_column(String(200))
    name_ko: Mapped[str] = mapped_column(String(200), default="")
    category: Mapped[str] = mapped_column(
        String(30), default="tourism",
    )  # medical, beauty, tourism, food, shopping
    description_ja: Mapped[str] = mapped_column(Text, default="")
    address: Mapped[str] = mapped_column(String(300), default="")
    latitude: Mapped[float] = mapped_column(Float, default=0.0)
    longitude: Mapped[float] = mapped_column(Float, default=0.0)
    avg_price_krw: Mapped[int] = mapped_column(default=0)
    rating: Mapped[float] = mapped_column(Float, default=0.0)
    popularity_score: Mapped[float] = mapped_column(Float, default=0.0)
    tags: Mapped[str] = mapped_column(
        Text, default="",
    )  # 쉼표 구분: "整形,二重,大邱"
    is_active: Mapped[bool] = mapped_column(default=True)
    partner_id: Mapped[str | None] = mapped_column(
        String(36), nullable=True, default=None,
    )  # partners 테이블 연결 (있으면)
