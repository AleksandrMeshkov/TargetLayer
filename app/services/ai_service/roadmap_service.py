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
            user_id=user_id or 1,  # Default to user 1 if not provided
            title=ai_response.goal_title,
            description=ai_response.goal_description
        )
        self.db.add(goal)
        await self.db.flush()
        
        # Create roadmap for the goal
        roadmap = Roadmap(
            goals_id=goal.goals_id,
            completed=False
        )
        self.db.add(roadmap)
        await self.db.flush()
        
        # Create tasks for the roadmap
        for i, ai_task in enumerate(ai_response.tasks):
            deadline = start_date + timedelta(days=ai_task.deadline_offset_days)
            
            task = Task(
                roadmap_id=roadmap.roadmap_id,
                title=ai_task.title,
                description=ai_task.description,
                order_index=i,
                deadline_end=deadline
            )
            self.db.add(task)
        
        await self.db.commit()
        await self.db.refresh(goal)
        
        logger.info(f"Created roadmap: '{goal.title}' with {len(ai_response.tasks)} tasks")
        return goal