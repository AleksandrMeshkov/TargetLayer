from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database.database import get_db
from app.schemas.password_recovery import (
    PasswordRecoveryRequestSchema,
    PasswordRecoveryConfirmSchema,
    PasswordRecoveryResponseSchema
)
from app.services.password.password_recovery_service import PasswordRecoveryService

router = APIRouter(prefix="/password", tags=["password-recovery"])


@router.post(
    "/forgot",
    status_code=status.HTTP_200_OK,
    response_model=PasswordRecoveryResponseSchema,
    summary="Запросить восстановление пароля"
)
async def request_password_recovery(
    request: PasswordRecoveryRequestSchema,
    db: AsyncSession = Depends(get_db)
):
    
    try:
        recovery_service = PasswordRecoveryService(db)
        await recovery_service.create_recovery(request.email)

        return PasswordRecoveryResponseSchema(
            status="success",
            message="Письмо с ссылкой восстановления отправлено на вашу почту",
            email=request.email,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при обработке запроса восстановления: {str(e)}",
        )


@router.post(
    "/recover",
    status_code=status.HTTP_200_OK,
    summary="Восстановить пароль по токену"
)
async def recover_password(
    request: PasswordRecoveryConfirmSchema,
    token: str = Query(...),
    db: AsyncSession = Depends(get_db)
):
    try:
        recovery_service = PasswordRecoveryService(db)
        await recovery_service.recover_password(token, request.new_password)

        return {
            "status": "success",
            "message": "Пароль успешно восстановлен. Вы можете войти с новым паролем",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при восстановлении пароля: {str(e)}",
        )
