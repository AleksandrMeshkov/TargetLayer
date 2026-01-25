from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class TaskResponse(BaseModel):
    task_id: int
    title: str
    description: Optional[str] = None
    order_index: int
    completed: bool
    completed_at: Optional[datetime] = None
    deadline_start: Optional[datetime] = None
    deadline_end: Optional[datetime] = None

    class Config:
        from_attributes = True


class GoalResponse(BaseModel):
    goals_id: int
    title: str
    description: Optional[str] = None

    class Config:
        from_attributes = True


class RoadmapResponse(BaseModel):
    roadmap_id: int
    goal: GoalResponse
    task: TaskResponse
    completed: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RoadmapsListResponse(BaseModel):
    roadmaps: list[RoadmapResponse]
    total: int

    class Config:
        from_attributes = True
