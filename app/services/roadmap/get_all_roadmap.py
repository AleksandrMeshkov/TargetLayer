from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload

from app.core.database.database import get_db
from app.core.security.jwt import JWTManager
from app.models.roadmap import Roadmap
from app.models.goal import Goal
from app.models.roadmap_copy import RoadmapCopy

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

    # Показываем только личные роудмапы пользователя:
    # 1. Созданные самим (Goal.user_id == user_id)
    # 2. Скопированные (есть запись в RoadmapCopy с user_id)
    
    # Получаем скопированные роудмапы
    copies_stmt = select(RoadmapCopy.new_roadmap_id).where(RoadmapCopy.user_id == user_id)
    copies_result = await db.execute(copies_stmt)
    copied_roadmap_ids = copies_result.scalars().all()

    # Строим условие поиска
    conditions = [Goal.user_id == user_id]  # Созданные самим
    
    if copied_roadmap_ids:
        conditions.append(Roadmap.roadmap_id.in_(copied_roadmap_ids))  # Скопированные

    stmt = (
        select(Roadmap)
        .join(Goal, Goal.goals_id == Roadmap.goals_id)
        .options(selectinload(Roadmap.tasks), selectinload(Roadmap.goal))
        .where(or_(*conditions))
        .order_by(Roadmap.updated_at.desc())
    )

    result = await db.execute(stmt)
    return list(result.scalars().unique().all())
