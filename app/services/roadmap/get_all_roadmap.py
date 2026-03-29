from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database.database import get_db
from app.core.security.jwt import JWTManager
from app.models.roadmap import Roadmap
from app.models.roadmap_access import RoadmapAccess

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

    stmt = (
        select(Roadmap)
        .join(RoadmapAccess, RoadmapAccess.roadmap_id == Roadmap.roadmap_id)
        .options(selectinload(Roadmap.tasks), selectinload(Roadmap.goal))
        .where(RoadmapAccess.user_id == user_id, RoadmapAccess.permission.in_(["viewer", "editor", "owner"]))
        .order_by(Roadmap.updated_at.desc())
    )

    result = await db.execute(stmt)
    return list(result.scalars().unique().all())
