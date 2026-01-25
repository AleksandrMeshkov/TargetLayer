from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database.database import get_db
from app.core.security.jwt import JWTManager
from app.models.user_roadmap import UserRoadmap
from app.models.user import User

security = HTTPBearer()
jwt_manager = JWTManager()


async def get_current_user_roadmap(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> UserRoadmap:
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
    
    from sqlalchemy.orm import selectinload
    stmt = select(UserRoadmap).options(
        selectinload(UserRoadmap.user)
    ).where(UserRoadmap.user_activity_id == user_activity_id)
    
    result = await db.execute(stmt)
    user_roadmap = result.scalars().first()
    
    if not user_roadmap:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User roadmap not found"
        )
    
    return user_roadmap


async def get_current_user(
    user_roadmap: UserRoadmap = Depends(get_current_user_roadmap)
) -> User:
    return user_roadmap.user