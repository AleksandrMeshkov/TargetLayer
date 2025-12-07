from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, ForeignKey
from .base import Base

class ChatMessage(Base):
    __tablename__ = "chat_messages"

    chat_messages_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    message_id: Mapped[int] = mapped_column(Integer, ForeignKey("messages.messages_id"), nullable=False)
    chat_id: Mapped[int] = mapped_column(Integer, ForeignKey("chats.chat_id"), nullable=False)

    message: Mapped["Message"] = relationship("Message", back_populates="chat_messages")
    chat: Mapped["Chat"] = relationship("Chat", back_populates="chat_messages")