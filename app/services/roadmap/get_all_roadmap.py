from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database.database import get_db
from app.core.security.jwt import JWTManager
from app.models.roadmap import Roadmap

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
        .options(selectinload(Roadmap.tasks), selectinload(Roadmap.goal))
        .order_by(Roadmap.updated_at.desc())
    )

    result = await db.execute(stmt)
    return list(result.scalars().all())
