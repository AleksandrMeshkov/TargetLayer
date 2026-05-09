from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.core.database.database import get_db
from app.core.security.jwt import JWTManager
from app.models.roadmap import Roadmap
from app.models.goal import Goal
from app.models.roadmap_copy import RoadmapCopy

security = HTTPBearer()
jwt_manager = JWTManager()


async def delete_user_roadmap(
    roadmap_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> dict:
    try:
        sub = jwt_manager.verify_access_token(credentials.credentials)
        user_id = int(sub)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        )
    
    roadmap_stmt = select(Roadmap).where(Roadmap.roadmap_id == roadmap_id)
    roadmap_result = await db.execute(roadmap_stmt)
    roadmap = roadmap_result.scalars().first()
    
    if not roadmap:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Роудмап не найден"
        )
    
    # Проверяем создателя роудмапа
    goal_stmt = select(Goal).where(Goal.goals_id == roadmap.goals_id)
    goal_result = await db.execute(goal_stmt)
    goal = goal_result.scalars().first()
    
    is_creator = goal and goal.user_id == user_id
    
    if is_creator:
        # Создатель удаляет оригинальный роудмап
        # Удаляем только саму запись о копировании, но копии остаются у пользователей
        await db.execute(
            delete(RoadmapCopy).where(RoadmapCopy.original_roadmap_id == roadmap_id)
        )
        # Теперь удаляем сам роудмап
        await db.delete(roadmap)
        await db.commit()
        return {
            "status": "success",
            "message": "Roadmap deleted successfully",
            "roadmap_id": roadmap_id
        }
    
    # Проверяем, это копия пользователя?
    copy_stmt = select(RoadmapCopy).where(
        RoadmapCopy.new_roadmap_id == roadmap_id,
        RoadmapCopy.user_id == user_id
    )
    copy_result = await db.execute(copy_stmt)
    copy_record = copy_result.scalars().first()
    
    if copy_record:
        # Пользователь удаляет свою копию
        # Удаляем запись копирования и сам роудмап-копию
        await db.delete(copy_record)
        await db.delete(roadmap)
        await db.commit()
        return {
            "status": "success",
            "message": "Roadmap copy deleted successfully",
            "roadmap_id": roadmap_id
        }
    
    # Не создатель и не скопировал - нет доступа
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Вы можете удалить только свой роудмап или его копию"
    )
