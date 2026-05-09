from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from app.models.roadmap import Roadmap
from app.models.goal import Goal
from app.models.task import Task
from app.models.team_member import TeamMember


async def get_tasks_for_roadmap(
    db: AsyncSession,
    user_id: int,
    roadmap_id: int,
) -> List[Task]:
    stmt = select(Roadmap).options(selectinload(Roadmap.tasks)).where(Roadmap.roadmap_id == roadmap_id)
    result = await db.execute(stmt)
    roadmap = result.scalars().first()

    if not roadmap:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Роудмап не найден")

    # Проверяем доступ: создатель или член команды
    goal_stmt = select(Goal).where(Goal.goals_id == roadmap.goals_id)
    goal_res = await db.execute(goal_stmt)
    goal = goal_res.scalars().first()
    
    # Может видеть если создатель
    if goal and goal.user_id == user_id:
        return list(roadmap.tasks)

    # Ор если роудмап в команде
    if roadmap.team_id:
        team_member_stmt = select(TeamMember).where(
            TeamMember.team_id == roadmap.team_id,
            TeamMember.user_id == user_id
        )
        team_member_res = await db.execute(team_member_stmt)
        if team_member_res.scalars().first():
            return list(roadmap.tasks)

    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="У вас нет доступа к этой дорожной карте")
