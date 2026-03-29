from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from app.models.roadmap import Roadmap
from app.models.roadmap_access import RoadmapAccess
from app.models.task import Task


async def get_tasks_for_roadmap(
    db: AsyncSession,
    user_id: int,
    roadmap_id: int,
) -> List[Task]:
    access_stmt = select(RoadmapAccess).where(
        RoadmapAccess.roadmap_id == roadmap_id,
        RoadmapAccess.user_id == user_id,
        RoadmapAccess.permission.in_(["viewer", "editor", "owner"]),
    )
    access_result = await db.execute(access_stmt)
    access = access_result.scalars().first()

    if not access:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="У вас нет доступа к этой дорожной карте")

    stmt = select(Roadmap).options(selectinload(Roadmap.tasks)).where(Roadmap.roadmap_id == roadmap_id)
    result = await db.execute(stmt)
    roadmap = result.scalars().first()

    if not roadmap:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Роудмап не найден")

    return list(roadmap.tasks)
