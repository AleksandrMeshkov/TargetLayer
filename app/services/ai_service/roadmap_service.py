import logging
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.goal import Goal
from app.models.task import Task
from app.models.roadmap import Roadmap
from app.schemas.ai_schemas import AIResponse

logger = logging.getLogger(__name__)


class RoadmapService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_from_ai(self, ai_response: AIResponse, user_id: int = None) -> Goal:
        start_date = datetime.utcnow()
        
        goal = Goal(
            title=ai_response.goal_title,
            description=ai_response.goal_description
        )
        self.db.add(goal)
        await self.db.flush()
        
        for i, ai_task in enumerate(ai_response.tasks):
            deadline = start_date + timedelta(days=ai_task.deadline_offset_days)
            
            task = Task(
                title=ai_task.title,
                description=ai_task.description,
                order_index=i,
                deadline_end=deadline
            )
            self.db.add(task)
            await self.db.flush()
            
            roadmap = Roadmap(
                goals_id=goal.goals_id,
                tasks_id=task.task_id
            )
            self.db.add(roadmap)
        
        await self.db.commit()
        await self.db.refresh(goal)
        
        logger.info(f"Created roadmap: '{goal.title}' with {len(ai_response.tasks)} tasks")
        return goal