"""AI conversation log model."""

import enum

from sqlalchemy import Enum, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.base import TimestampMixin


class ConversationContext(str, enum.Enum):
    CHAT = "chat"
    QUERY = "query"
    CONTENT = "content"
    TRANSLATION = "translation"


class AIConversation(Base, TimestampMixin):
    __tablename__ = "ai_conversations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    context: Mapped[ConversationContext] = mapped_column(
        Enum(ConversationContext, name="conversation_context"),
        nullable=False,
    )
    messages: Mapped[dict] = mapped_column(JSONB, default=list, nullable=False)
    model_used: Mapped[str] = mapped_column(String(100), nullable=False)
    tokens_used: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
