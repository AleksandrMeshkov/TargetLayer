from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from app.models.roadmap import Roadmap
from app.models.goal import Goal
from app.models.task import Task


async def get_tasks_for_roadmap(
    db: AsyncSession,
    user_id: int,
    roadmap_id: int,
) -> List[Task]:
    stmt = select(Roadmap).options(selectinload(Roadmap.tasks)).where(Roadmap.roadmap_id == roadmap_id)
    result = await db.execute(stmt)
    roadmap = result.scalars().first()

    if not roadmap:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Roadmap not found")

    goal_stmt = select(Goal).where((Goal.goals_id == roadmap.goals_id) & (Goal.user_id == user_id))
    goal_result = await db.execute(goal_stmt)
    goal = goal_result.scalars().first()

    if not goal:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You don't have access to this roadmap")

    return list(roadmap.tasks)
