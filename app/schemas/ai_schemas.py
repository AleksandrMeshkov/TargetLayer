from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class AITaskResponse(BaseModel):
    title: str = Field(..., min_length=3, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    order_index: int = Field(default=0, ge=0)
    deadline_offset_days: int = Field(..., ge=0, le=365)

    model_config = {"from_attributes": True}


class AIRoadmapResponse(BaseModel):
    goal_title: str = Field(..., min_length=3, max_length=255)
    goal_description: Optional[str] = Field(None, max_length=2000)
    tasks: List[AITaskResponse] = Field(..., min_items=1, max_items=20)

    model_config = {"from_attributes": True}


class AIRoadmapRequest(BaseModel):
    prompt: str = Field(..., min_length=5, max_length=1000, description="Описание цели")

    model_config = {"from_attributes": True}


class RoadmapSaveRequest(BaseModel):
    goal_title: str = Field(..., min_length=3, max_length=255)
    goal_description: Optional[str] = Field(None, max_length=2000)
    tasks: List[AITaskResponse] = Field(..., min_items=1)

    model_config = {"from_attributes": True}


class DraftRoadmapResponse(BaseModel):
    """Черновик roadmap с draft_id для дальнейшего редактирования."""
    draft_id: int
    goal_title: str
    goal_description: Optional[str] = None
    tasks: List[AITaskResponse]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DraftUpdateRequest(BaseModel):
    """Запрос на обновление черновика с новым prompt."""
    prompt: str = Field(..., min_length=5, max_length=1000)

    model_config = {"from_attributes": True}
