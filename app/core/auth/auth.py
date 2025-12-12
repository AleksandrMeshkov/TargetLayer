from datetime import datetime, timedelta
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.settings.settings import settings
from app.core.database import get_db
from app.models.auth_identity import AuthIdentity
from app.models.provider import Provider

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

async def get_user_activity_id_from_token(token: str) -> int:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_activity_id = payload.get("sub")
        if user_activity_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return int(user_activity_id)
    except (JWTError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_current_user_activity_id(token: str = Depends(oauth2_scheme)) -> int:
    return await get_user_activity_id_from_token(token)

async def get_email_provider_id(db: AsyncSession) -> int:
    result = await db.execute(select(Provider).where(Provider.name == "email"))
    provider = result.scalar_one_or_none()
    if not provider:
        raise RuntimeError("Email provider not found in database")
    return provider.provider_id