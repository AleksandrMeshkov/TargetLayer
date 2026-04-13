from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.core.database.database import get_db
from app.core.security.jwt import JWTManager
from app.models.roadmap import Roadmap
from app.models.roadmap_access import RoadmapAccess

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
    
    access_stmt = select(RoadmapAccess).where(
        (RoadmapAccess.roadmap_id == roadmap.roadmap_id)
        & (RoadmapAccess.user_id == user_id)
        & (RoadmapAccess.permission == "owner")
    )
    access_result = await db.execute(access_stmt)
    access = access_result.scalars().first()
    
    if not access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Дорожная карта не найдена или у вас нет разрешения на ее удаление"
        )

    await db.execute(
        delete(RoadmapAccess).where(RoadmapAccess.roadmap_id == roadmap.roadmap_id)
    )
    await db.delete(roadmap)
    await db.commit()
    
    return {
        "status": "success",
        "message": "Roadmap deleted successfully",
        "roadmap_id": roadmap_id
    }
