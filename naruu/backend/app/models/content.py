"""Content (video/brochure) model."""

import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Enum, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.base import TimestampMixin


class ContentSeries(str, enum.Enum):
    DAEGU_TOUR = "DaeguTour"
    JCOUPLE = "JCouple"
    MEDICAL = "Medical"
    BROCHURE = "Brochure"


class ContentStatus(str, enum.Enum):
    DRAFT = "draft"
    REVIEW = "review"
    APPROVED = "approved"
    PUBLISHED = "published"
    REJECTED = "rejected"


class ContentPlatform(str, enum.Enum):
    YOUTUBE = "youtube"
    INSTAGRAM = "instagram"
    TIKTOK = "tiktok"


class Content(Base, TimestampMixin):
    __tablename__ = "contents"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    series: Mapped[ContentSeries] = mapped_column(
        Enum(ContentSeries, name="content_series"),
        nullable=False,
    )
    script_ja: Mapped[str | None] = mapped_column(Text)
    script_ko: Mapped[str | None] = mapped_column(Text)
    status: Mapped[ContentStatus] = mapped_column(
        Enum(ContentStatus, name="content_status"),
        default=ContentStatus.DRAFT,
        nullable=False,
    )
    video_url: Mapped[str | None] = mapped_column(String(500))
    thumbnail_url: Mapped[str | None] = mapped_column(String(500))
    platform: Mapped[ContentPlatform | None] = mapped_column(
        Enum(ContentPlatform, name="content_platform"),
    )
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    performance_metrics: Mapped[dict | None] = mapped_column(JSONB)
