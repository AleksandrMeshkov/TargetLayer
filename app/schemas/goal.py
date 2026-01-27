from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class GoalCreate(BaseModel):
    title: str
    description: str | None = None

class GoalUpdate(BaseModel):
    title: str
    description: str | None = None

class GoalResponse(BaseModel):
    goals_id: int
    user_id: int
    title: str
    description: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True