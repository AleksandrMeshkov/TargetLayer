from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .ai_message import AIMessage


class AIMessageRole(Base):
    __tablename__ = "ai_message_role"

    ai_message_role_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)

    messages: Mapped[list["AIMessage"]] = relationship("AIMessage", back_populates="ai_message_role")
