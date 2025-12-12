from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.schemas.auth import UserRegister, Token
from app.core.auth import create_access_token, get_password_hash, verify_password, get_email_provider_id
from app.core.database import get_db
from app.models.user import User
from app.models.user_activity import UserActivity
from app.models.auth_identity import AuthIdentity
from app.models.provider import Provider
from fastapi import APIRouter

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(user: UserRegister, db: AsyncSession = Depends(get_db)):
    
    existing = await db.execute(
        select(AuthIdentity).where(AuthIdentity.email == user.email)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    db_user = User(
        username=user.username,
        name=user.name,
        surname=user.surname,
        patronymic=user.patronymic,
        email_verified=False,
        avatar_url=None
    )
    db.add(db_user)
    await db.flush()

    db_activity = UserActivity(user_id=db_user.user_id)
    db.add(db_activity)
    await db.flush()

    provider_id = await get_email_provider_id(db)
    db_auth = AuthIdentity(
        user_activity_id=db_activity.user_activity_id,
        provider_id=provider_id,
        email=user.email,
        password_hash=get_password_hash(user.password)
    )
    db.add(db_auth)
    await db.commit()

    access_token = create_access_token(data={"sub": str(db_activity.user_activity_id)})
    return Token(access_token=access_token)

@router.post("/login", response_model=Token)
async def login(email: str, password: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(AuthIdentity)
        .join(AuthIdentity.provider)
        .where(AuthIdentity.email == email, Provider.name == "email")
    )
    auth = result.scalar_one_or_none()
    if not auth or not verify_password(password, auth.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    access_token = create_access_token(data={"sub": str(auth.user_activity_id)})
    return Token(access_token=access_token)