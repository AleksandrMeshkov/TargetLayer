from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, ForeignKey
from .base import Base

class ChatParticipant(Base):
    __tablename__ = "chat_participants"

    chat_id: Mapped[int] = mapped_column(Integer, ForeignKey("chats.chat_id"), primary_key=True)
    user_activity_id: Mapped[int] = mapped_column(Integer, ForeignKey("user_activity.user_activity_id"), primary_key=True)

    chat: Mapped["Chat"] = relationship("Chat", back_populates="participants")
    user_activity: Mapped["UserActivity"] = relationship("UserActivity", back_populates="chats")