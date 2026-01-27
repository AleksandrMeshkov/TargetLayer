from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Text, DateTime, Integer, ForeignKey
from typing import Optional
from datetime import datetime
from .base import Base


class Message(Base):
    __tablename__ = "messages"
    
    message_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True) 
    chat_id: Mapped[int] = mapped_column(Integer, ForeignKey("chats.chat_id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    
    chat: Mapped["Chat"] = relationship("Chat", back_populates="messages")
    user: Mapped["User"] = relationship("User", back_populates="messages")