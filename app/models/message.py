from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Text, DateTime
from typing import Optional
from datetime import datetime
from .base import Base



class Message(Base):
    __tablename__ = "messages"
    messages_id: Mapped[int] = mapped_column(primary_key=True) 
    content: Mapped[str] = mapped_column(Text, nullable=False)
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    
    chat_messages: Mapped[list["ChatMessage"]] = relationship("ChatMessage", back_populates="message")