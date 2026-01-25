from pydantic import BaseModel

class GoalCreate(BaseModel):
    title: str
    description: str | None = None

class GoalUpdate(BaseModel):
    title: str
    description: str | None = None

class GoalResponse(GoalCreate):
    goals_id: int
    completed: bool

    class Config:
        from_attributes = True