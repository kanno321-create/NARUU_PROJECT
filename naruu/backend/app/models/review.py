"""Customer review model."""

import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.base import TimestampMixin


class ReviewPlatform(str, enum.Enum):
    GOOGLE = "google"
    INSTAGRAM = "instagram"
    LINE = "line"
    NAVER = "naver"


class Review(Base, TimestampMixin):
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    customer_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("customers.id"), index=True
    )
    partner_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("partners.id")
    )
    platform: Mapped[ReviewPlatform] = mapped_column(
        Enum(ReviewPlatform, name="review_platform"),
        nullable=False,
    )
    rating: Mapped[float | None] = mapped_column(Float)
    content_ja: Mapped[str | None] = mapped_column(Text)
    content_ko: Mapped[str | None] = mapped_column(Text)
    sentiment_score: Mapped[float | None] = mapped_column(Float)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    response_text: Mapped[str | None] = mapped_column(Text)
    responded_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
