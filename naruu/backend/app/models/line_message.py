"""LINE message log model."""

import enum

from sqlalchemy import Boolean, Enum, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.base import TimestampMixin


class MessageDirection(str, enum.Enum):
    IN = "in"
    OUT = "out"


class MessageType(str, enum.Enum):
    TEXT = "text"
    IMAGE = "image"
    TEMPLATE = "template"
    STICKER = "sticker"


class LineMessage(Base, TimestampMixin):
    __tablename__ = "line_messages"
    __table_args__ = (
        Index("ix_line_messages_created_at", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    line_user_id: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    customer_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("customers.id", ondelete="CASCADE"),
        index=True,
    )
    direction: Mapped[MessageDirection] = mapped_column(
        Enum(MessageDirection, name="message_direction"),
        nullable=False,
        index=True,
    )
    message_type: Mapped[MessageType] = mapped_column(
        Enum(MessageType, name="message_type"),
        default=MessageType.TEXT,
        nullable=False,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    ai_generated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
