from typing import Optional

from fastapi import Depends, HTTPException, status, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database.database import get_db
from app.core.security.jwt import JWTManager
from app.models.user import User

security = HTTPBearer()
security_optional = HTTPBearer(auto_error=False)
jwt_manager = JWTManager()


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security_optional),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    if not credentials:
        return None

    try:
        sub = jwt_manager.verify_access_token(credentials.credentials)
        user_id = int(sub)
    except Exception:
        return None

    stmt = select(User).where(User.user_id == user_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    try:
        sub = jwt_manager.verify_access_token(credentials.credentials)
        user_id = int(sub)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        )

    stmt = select(User).where(User.user_id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return user