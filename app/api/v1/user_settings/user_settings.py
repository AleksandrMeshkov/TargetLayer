from fastapi import APIRouter, Depends, HTTPException, status, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.get_my_user import get_current_user
from app.core.database.database import get_db
from app.schemas.update_user import UserNameSchema, UserPublicSchema, UserUpdateSchema
from app.services.update_username import UserService
from app.models.user import User

router = APIRouter(prefix="/user", tags=["user"])
security = HTTPBearer()


@router.get("/profile", response_model=UserPublicSchema, openapi_extra={"security": [{"Bearer": []}]})
async def get_profile(
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
    update_data: UserUpdateSchema,
    credentials: HTTPAuthorizationCredentials = Security(security),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        user_service = UserService(db)
        
        if any([update_data.name, update_data.surname, update_data.patronymic]):
            name_data = UserNameSchema(
                name=update_data.name or current_user.name,
                surname=update_data.surname or current_user.surname,
                patronymic=update_data.patronymic if update_data.patronymic is not None else current_user.patronymic
            )
            await user_service.update_user_name(current_user.user_id, name_data)
        
        if update_data.avatar_url is not None:
            current_user.avatar_url = update_data.avatar_url
            await db.commit()
            await db.refresh(current_user)
        
        return current_user
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