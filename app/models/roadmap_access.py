from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class RoadmapAccess(Base):
    __tablename__ = "roadmap_access"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    roadmap_id: Mapped[int] = mapped_column(Integer, ForeignKey("roadmaps.roadmap_id", ondelete="CASCADE"), nullable=False, index=True)
    permission: Mapped[str] = mapped_column(String(32), default="viewer", nullable=False)

    roadmap: Mapped["Roadmap"] = relationship("Roadmap", back_populates="access_entries")
    user: Mapped["User"] = relationship("User", back_populates="roadmap_access_entries")
