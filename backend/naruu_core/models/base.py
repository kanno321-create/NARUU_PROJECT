"""SQLAlchemy 베이스 모델 + 공통 믹스인."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class NaruuBase(DeclarativeBase):
    """모든 NARUU 모델의 베이스 클래스."""

    pass


class TimestampMixin:
    """created_at, updated_at 자동 관리 믹스인."""

    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        onupdate=func.now(),
    )
