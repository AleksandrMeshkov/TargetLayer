from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, DateTime, func
from datetime import datetime
from .base import Base

class Chat(Base):
    __tablename__ = "chats"

    chat_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user_activities: Mapped[list["UserActivity"]] = relationship("UserActivity", secondary="chat_participants", back_populates="chats")
    messages: Mapped[list["Message"]] = relationship("Message", back_populates="chat")
    chat_messages: Mapped[list["ChatMessage"]] = relationship("ChatMessage", back_populates="chat")