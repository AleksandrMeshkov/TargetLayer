from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from fastapi import HTTPException, status

from app.models.roadmap import Roadmap
from app.models.roadmap_access import RoadmapAccess
from app.services.team_service.get_owned_team import get_owned_team
from app.models.user import User


async def delete_team_roadmap(db: AsyncSession, user: User, team_id: int, roadmap_id: int) -> dict:
    team = await get_owned_team(db, user, team_id)

    stmt = select(Roadmap).where(Roadmap.roadmap_id == roadmap_id, Roadmap.team_id == team.team_id)
    res = await db.execute(stmt)
    roadmap = res.scalars().first()

    if not roadmap:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Роудмап не найден в команде")

    roadmap.team_id = None
    db.add(roadmap)

    await db.execute(delete(RoadmapAccess).where(RoadmapAccess.roadmap_id == roadmap_id))

    await db.commit()

    return {"status": "success", "message": "Роудмап удалён из команды"}
