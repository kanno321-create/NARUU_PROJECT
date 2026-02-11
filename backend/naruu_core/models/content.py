"""콘텐츠 + 스케줄 모델."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from naruu_core.models.base import NaruuBase, TimestampMixin


class Content(NaruuBase, TimestampMixin):
    """자동 생성 콘텐츠 (동영상, 블로그 등).

    파이프라인: script → image → voice → video → publish
    """

    __tablename__ = "contents"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4()),
    )
    title: Mapped[str] = mapped_column(String(300), default="")
    content_type: Mapped[str] = mapped_column(
        String(20), default="video",
    )  # video, blog, sns
    language: Mapped[str] = mapped_column(String(5), default="ja")
    topic: Mapped[str] = mapped_column(String(200), default="")
    script: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(
        String(20), default="draft",
    )  # draft → scripted → produced → published → archived
    pipeline_stage: Mapped[str] = mapped_column(
        String(20), default="pending",
    )  # pending, script, image, voice, video, publish, done, failed
    cost_usd: Mapped[float] = mapped_column(default=0.0)
    publish_url: Mapped[str] = mapped_column(String(500), default="")
    error_message: Mapped[str] = mapped_column(Text, default="")
    metadata_json: Mapped[str] = mapped_column(Text, default="{}")


class ContentSchedule(NaruuBase, TimestampMixin):
    """콘텐츠 발행 스케줄."""

    __tablename__ = "content_schedules"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4()),
    )
    name: Mapped[str] = mapped_column(String(200))
    content_type: Mapped[str] = mapped_column(String(20), default="video")
    topic_template: Mapped[str] = mapped_column(String(300), default="")
    language: Mapped[str] = mapped_column(String(5), default="ja")
    cron_expression: Mapped[str] = mapped_column(
        String(50), default="0 9 * * 1",
    )  # 매주 월요일 09:00
    is_active: Mapped[bool] = mapped_column(default=True)
    last_run_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True, default=None,
    )
