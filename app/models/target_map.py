from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, ForeignKey
from .base import Base

class TargetMap(Base):
    __tablename__ = "target_map"

    target_map_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(Integer, ForeignKey("tasks.task_id"), nullable=False)
    goals_id: Mapped[int] = mapped_column(Integer, ForeignKey("goals.goals_id"), nullable=False)

    task: Mapped["Task"] = relationship("Task", back_populates="target_maps")
    goal: Mapped["Goal"] = relationship("Goal", back_populates="target_maps")