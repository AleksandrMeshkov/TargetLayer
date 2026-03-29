from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, Text, DateTime, ForeignKey
from datetime import datetime
from typing import TYPE_CHECKING

from .base import Base

if TYPE_CHECKING:
    from .ai_conversation import AIConversation
    from .ai_message_role import AIMessageRole


class AIMessage(Base):
    __tablename__ = "ai_messages"

    message_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    conversation_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("ai_conversations.conversation_id", ondelete="CASCADE"), nullable=False, index=True
    )
    ai_message_role_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("ai_message_role.ai_message_role_id", ondelete="RESTRICT"), nullable=False, index=True
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    conversation: Mapped["AIConversation"] = relationship(
        "AIConversation", back_populates="messages"
    )
    ai_message_role: Mapped["AIMessageRole"] = relationship("AIMessageRole", back_populates="messages")
