from fastapi import APIRouter, Depends, HTTPException, status, Response, Cookie
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.auth import UserRegister, Token
from app.services.user.auth_service import AuthService
from app.core.database.database import get_db
from app.core.settings.settings import settings

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=Token)
async def register(user: UserRegister, response: Response, db: AsyncSession = Depends(get_db)):
    try:
        auth_service = AuthService(db)
        user_id = await auth_service.register_email(
            user.email, user.password, user.username, user.name, user.surname, user.patronymic
        )
        tokens = await auth_service.create_tokens(user_id)
        refresh = tokens.get("refresh_token")
        if refresh:
            max_age = settings.REFRESH_TOKEN_EXPIRE_HOURS * 3600
            response.set_cookie(
                key="refresh_token",
                value=refresh,
                httponly=True,
                samesite="lax",
                max_age=max_age,
            )
        tokens["refresh_token"] = None
        return tokens
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/login", response_model=Token)
async def login(email: str, password: str, response: Response, db: AsyncSession = Depends(get_db)):
    auth_service = AuthService(db)
    user_id = await auth_service.authenticate_email(email, password)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    tokens = await auth_service.create_tokens(user_id)
    refresh = tokens.get("refresh_token")
    if refresh:
        max_age = settings.REFRESH_TOKEN_EXPIRE_HOURS * 3600
        response.set_cookie(
            key="refresh_token",
            value=refresh,
            httponly=True,
            samesite="lax",
            max_age=max_age,
        )
    tokens["refresh_token"] = None
    return tokens

@router.post("/refresh", response_model=Token)
async def refresh(response: Response, refresh_token: str | None = Cookie(None)):
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Missing refresh token")
    auth_service = AuthService(None)  # db not used
    tokens = await auth_service.refresh_tokens(refresh_token)
    if not tokens:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    refresh = tokens.get("refresh_token")
    if refresh:
        max_age = settings.REFRESH_TOKEN_EXPIRE_HOURS * 3600
        response.set_cookie(
            key="refresh_token",
            value=refresh,
            httponly=True,
            samesite="lax",
            max_age=max_age,
        )
    tokens["refresh_token"] = None
    return tokens