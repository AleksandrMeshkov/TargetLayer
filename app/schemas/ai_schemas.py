from pydantic import BaseModel, Field
from typing import Optional, List


class AITaskCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=255)
    description: str = Field(..., min_length=10, max_length=1000)
    estimated_duration_days: int = Field(..., ge=1, le=365)
    deadline_offset_days: int = Field(..., ge=0, le=365)
    priority: str = Field("medium", pattern="^(high|medium|low)$")
    resources: List[str] = Field(default_factory=list)


class AIResponse(BaseModel):
    goal_title: str = Field(..., min_length=3, max_length=255)
    goal_description: str = Field(..., min_length=10, max_length=2000)
    tasks: List[AITaskCreate] = Field(..., min_items=1, max_items=10)


class GoalDecompositionRequest(BaseModel):
    goal: str = Field(..., min_length=5, max_length=500)
    timeframe_months: int = Field(..., ge=1, le=24)
    current_level: Optional[str] = None
    weekly_hours: Optional[int] = 10
