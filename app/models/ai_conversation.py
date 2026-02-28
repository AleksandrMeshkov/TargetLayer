from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, ForeignKey, DateTime
from datetime import datetime
from typing import List

from .base import Base


class AIConversation(Base):
    __tablename__ = "ai_conversations"

    conversation_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # one user owns this conversation
    user: Mapped["User"] = relationship("User", back_populates="ai_conversations")

    # One conversation contains many messages from both user and AI
    messages: Mapped[List["AIMessage"]] = relationship(
        "AIMessage", back_populates="conversation", cascade="all, delete-orphan"
    )
