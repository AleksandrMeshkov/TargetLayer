from pydantic import BaseModel, ConfigDict
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
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class GoalResponse(BaseModel):
    goals_id: int
    title: str
    description: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RoadmapResponse(BaseModel):
    roadmap_id: int
    goals_id: int
    goal: Optional[GoalResponse] = None
    tasks: list[TaskResponse] = []
    completed: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RoadmapsListResponse(BaseModel):
    roadmaps: list[RoadmapResponse]
    total: int

    model_config = ConfigDict(from_attributes=True)


class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    order_index: Optional[int] = 0
    deadline_start: Optional[datetime] = None
    deadline_end: Optional[datetime] = None

    model_config = ConfigDict()


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    order_index: Optional[int] = None
    deadline_start: Optional[datetime] = None
    deadline_end: Optional[datetime] = None
    completed: Optional[bool] = None

    model_config = ConfigDict()