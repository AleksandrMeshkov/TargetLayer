from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, ForeignKey
from .base import Base

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    
    chat_messages_id: Mapped[int] = mapped_column(primary_key=True)
    chat_id: Mapped[int] = mapped_column(Integer, ForeignKey("chats.chat_id"))
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.user_id"))
    message_id: Mapped[int] = mapped_column(Integer, ForeignKey("messages.messages_id"))
    
    chat: Mapped["Chat"] = relationship("Chat", back_populates="chat_messages")
    user: Mapped["User"] = relationship("User", back_populates="chat_messages")
    message: Mapped["Message"] = relationship("Message", back_populates="chat_messages")