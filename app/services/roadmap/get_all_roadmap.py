from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload

from app.core.database.database import get_db
from app.core.security.jwt import JWTManager
from app.models.roadmap import Roadmap
from app.models.goal import Goal
from app.models.team_member import TeamMember

security = HTTPBearer()
jwt_manager = JWTManager()


async def get_user_roadmaps(
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

    # Получаем роудмапы которые:
    # 1. Созданы самим пользователем (Goal.user_id == user_id)
    # 2. Или привязаны к команде, в которой состоит пользователь
    user_teams_stmt = select(TeamMember.team_id).where(TeamMember.user_id == user_id)
    user_teams = (await db.execute(user_teams_stmt)).scalars().all()

    stmt = (
        select(Roadmap)
        .join(Goal, Goal.goals_id == Roadmap.goals_id)
        .options(selectinload(Roadmap.tasks), selectinload(Roadmap.goal))
        .where(
            or_(
                Goal.user_id == user_id,  # Созданные самим пользователем
                Roadmap.team_id.in_(user_teams) if user_teams else False  # Или в его командах
            )
        )
        .order_by(Roadmap.updated_at.desc())
    )

    result = await db.execute(stmt)
    return list(result.scalars().unique().all())
