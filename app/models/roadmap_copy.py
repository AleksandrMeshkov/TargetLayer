from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class RoadmapCopy(Base):
    __tablename__ = "roadmap_copies"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    original_roadmap_id: Mapped[int] = mapped_column(Integer, ForeignKey("roadmaps.roadmap_id", ondelete="CASCADE"), nullable=False, index=True)
    new_roadmap_id: Mapped[int] = mapped_column(Integer, ForeignKey("roadmaps.roadmap_id", ondelete="CASCADE"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    original_roadmap: Mapped["Roadmap"] = relationship(
        "Roadmap", foreign_keys=[original_roadmap_id], back_populates="source_copies"
    )
    new_roadmap: Mapped["Roadmap"] = relationship(
        "Roadmap", foreign_keys=[new_roadmap_id], back_populates="copied_from"
    )
    user: Mapped["User"] = relationship("User")
