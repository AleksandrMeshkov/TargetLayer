from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database.database import get_db
from app.core.security.jwt import JWTManager
from app.models.user import User
from app.models.roadmap import Roadmap
from app.models.goal import Goal

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

    stmt = select(User).options(
        selectinload(User.goals).selectinload(Goal.roadmap).options(
            selectinload(Roadmap.tasks),
            selectinload(Roadmap.goal),
        )
    ).where(User.user_id == user_id)

    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    roadmaps: list[Roadmap] = []
    for goal in user.goals:
        if goal.roadmap:
            roadmaps.append(goal.roadmap)

    return roadmaps
