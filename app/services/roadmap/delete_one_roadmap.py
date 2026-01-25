from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.core.database.database import get_db
from app.core.security.jwt import JWTManager
from app.models.user_roadmap import UserRoadmap
from app.models.roadmap import Roadmap

security = HTTPBearer()
jwt_manager = JWTManager()


async def delete_user_roadmap(
    roadmap_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """
    Удалить выбранный роудмап текущего пользователя по токену и ID роудмапа.
    Проверяет, что роудмап принадлежит пользователю перед удалением.
    """
    token = credentials.credentials
    payload = jwt_manager.decode_token(token)
    
    if isinstance(payload, str):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=payload
        )
    
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type"
        )
    
    try:
        user_activity_id = int(payload.get("sub"))
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token subject"
        )
    
    # Проверяем, что роудмап принадлежит пользователю
    stmt = select(UserRoadmap).where(
        (UserRoadmap.user_activity_id == user_activity_id) &
        (UserRoadmap.roadmap_id == roadmap_id)
    )
    result = await db.execute(stmt)
    user_roadmap = result.scalars().first()
    
    if not user_roadmap:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Roadmap not found or you don't have permission to delete it"
        )
    
    # Удаляем все записи UserRoadmap связанные с этим роудмапом
    delete_stmt = delete(UserRoadmap).where(UserRoadmap.roadmap_id == roadmap_id)
    await db.execute(delete_stmt)
    
    # Удаляем сам роудмап
    roadmap_stmt = select(Roadmap).where(Roadmap.roadmap_id == roadmap_id)
    roadmap_result = await db.execute(roadmap_stmt)
    roadmap = roadmap_result.scalars().first()
    
    if roadmap:
        await db.delete(roadmap)
    
    await db.commit()
    
    return {
        "status": "success",
        "message": "Roadmap deleted successfully",
        "roadmap_id": roadmap_id
    }
