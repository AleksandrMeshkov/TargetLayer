from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.user.get_my_user import get_current_user
from app.core.database.database import get_db
from app.schemas.update_user import UserNameSchema, UserPublicSchema, UserSearchResponse
from app.services.user.search_username import search_users_by_username
from app.services.user.update_username import UserService
from app.models.user import User

router = APIRouter(prefix="/api/v1/user", tags=["user"])
security = HTTPBearer()


@router.get("/search", response_model=UserSearchResponse, openapi_extra={"security": [{"Bearer": []}]})
async def search_users(
    username: str,
    limit: int = 50,
    _current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    normalized_limit = max(1, min(limit, 100))
    users = await search_users_by_username(db, username, normalized_limit)
    return UserSearchResponse(users=users, total=len(users))


@router.get("/me", response_model=UserPublicSchema, openapi_extra={"security": [{"Bearer": []}]})
async def get_current_profile(
    credentials: HTTPAuthorizationCredentials = Security(security),
    current_user: User = Depends(get_current_user)
):
    return current_user


@router.put("/name", response_model=UserPublicSchema, openapi_extra={"security": [{"Bearer": []}]})
async def update_name(
    name_data: UserNameSchema,
    credentials: HTTPAuthorizationCredentials = Security(security),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        user_service = UserService(db)
        updated_user = await user_service.update_user_name(
            current_user.user_id, 
            name_data
        )
        return updated_user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/profile", response_model=UserPublicSchema, openapi_extra={"security": [{"Bearer": []}]})
async def update_profile(
    avatar: UploadFile = File(...),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        user_service = UserService(db)
        updated_user = await user_service.update_user_avatar(
            current_user.user_id,
            avatar
        )
        return updated_user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{user_id}", response_model=UserPublicSchema)
async def get_user_by_id(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    user_service = UserService(db)
    user = await user_service.get_user_profile(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user