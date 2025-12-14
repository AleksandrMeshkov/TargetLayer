from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.auth import UserRegister, Token
from app.services.auth_service import AuthService
from app.core.database.database import get_db

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=Token)
async def register(user: UserRegister, db: AsyncSession = Depends(get_db)):
    try:
        auth_service = AuthService(db)
        user_activity_id = await auth_service.register_email(
            user.email, user.password, user.username, user.name, user.surname
        )
        return await auth_service.create_tokens(user_activity_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/login", response_model=Token)
async def login(email: str, password: str, db: AsyncSession = Depends(get_db)):
    auth_service = AuthService(db)
    user_activity_id = await auth_service.authenticate_email(email, password)
    if not user_activity_id:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return await auth_service.create_tokens(user_activity_id)

@router.post("/refresh", response_model=Token)
async def refresh(refresh_token: str, db: AsyncSession = Depends(get_db)):
    auth_service = AuthService(db)
    tokens = await auth_service.refresh_tokens(refresh_token)
    if not tokens:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    return tokens