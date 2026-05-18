from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database.database import get_db
from app.core.security.jwt import JWTManager
from app.models.roadmap import Roadmap
from app.models.goal import Goal
from app.models.team_member import TeamMember
from app.models.roadmap_copy import RoadmapCopy

security = HTTPBearer()
jwt_manager = JWTManager()


async def get_team_available_roadmaps(
    team_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> list[Roadmap]:
    try:
        sub = jwt_manager.verify_access_token(credentials.credentials)
        user_id = int(sub)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        )

    member_stmt = select(TeamMember).where(
        TeamMember.team_id == team_id,
        TeamMember.user_id == user_id
    )
    member_result = await db.execute(member_stmt)
    if not member_result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Вы не состоите в этой команде"
        )

    copies_stmt = select(RoadmapCopy.new_roadmap_id).where(RoadmapCopy.user_id == user_id)
    copies_result = await db.execute(copies_stmt)
    copied_roadmap_ids = copies_result.scalars().all()

    where_conditions = [Roadmap.team_id == team_id]
    
    if copied_roadmap_ids:
        where_conditions.append(~Roadmap.roadmap_id.in_(copied_roadmap_ids))

    stmt = (
        select(Roadmap)
        .join(Goal, Goal.goals_id == Roadmap.goals_id)
        .options(selectinload(Roadmap.tasks), selectinload(Roadmap.goal))
        .where(*where_conditions)
        .order_by(Roadmap.updated_at.desc())
    )

    result = await db.execute(stmt)
    return list(result.scalars().unique().all())
