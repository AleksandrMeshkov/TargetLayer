from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.user.get_my_user import get_current_user
from app.core.database.database import get_db
from app.schemas.update_password_user import PasswordChangeSchema
from app.services.password.password_service import PasswordService
from app.models.user import User

router = APIRouter(prefix="/password", tags=["password"])
security = HTTPBearer()



@router.put("/change", status_code=status.HTTP_200_OK, openapi_extra={"security": [{"Bearer": []}]})
async def change_password(
    password_data: PasswordChangeSchema,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    
    try:
        password_service = PasswordService(db)
        
        await password_service.change_password_by_user_id(
            user_id=current_user.user_id,
            password_data=password_data
        )
        
        return {
            "message": "Пароль успешно изменен",
            "detail": "Пароль был захеширован и сохранен в базе данных"
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        print(f"Ошибка при изменении пароля: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Внутренняя ошибка сервера при изменении пароля"
        )