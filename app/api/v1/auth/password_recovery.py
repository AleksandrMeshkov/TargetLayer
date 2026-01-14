from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database.database import get_db
from app.schemas.password_recovery import (
    PasswordRecoveryRequestSchema,
    PasswordRecoveryConfirmSchema,
    PasswordRecoveryResponseSchema
)
from app.services.password_recovery_service import PasswordRecoveryService

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
    """
    Инициирует процесс восстановления пароля.
    
    Процесс:
    - Проверяет наличие пользователя с таким email
    - Генерирует криптографически стойкий токен
    - Сохраняет токен в БД с временем истечения (24 часа)
    - Отправляет письмо с токеном на email
    
    Параметры:
        email: Email адрес пользователя
    
    Возвращает:
        Статус успеха и сообщение
    
    Исключает:
        400: Пользователь не найден или ошибка при отправке письма
    """
    try:
        recovery_service = PasswordRecoveryService(db)
        recovery = await recovery_service.create_recovery(request.email)
        
        return PasswordRecoveryResponseSchema(
            status="success",
            message="Письмо с ссылкой восстановления отправлено на вашу почту",
            email=request.email
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при обработке запроса восстановления: {str(e)}"
        )


@router.post(
    "/recover",
    status_code=status.HTTP_200_OK,
    summary="Восстановить пароль по токену"
)
async def recover_password(
    request: PasswordRecoveryConfirmSchema,
    db: AsyncSession = Depends(get_db)
):
    """
    Завершает процесс восстановления пароля.
    
    Процесс:
    - Проверяет валидность токена
    - Проверяет что токен не истек и не использован
    - Хеширует новый пароль
    - Обновляет пароль в БД
    - Помечает токен как использованный
    
    Параметры:
        token: Токен из письма восстановления
        new_password: Новый пароль
        confirm_password: Подтверждение пароля
    
    Возвращает:
        Статус успеха
    
    Исключает:
        400: Токен не найден, истек, уже использован или пароли не совпадают
    """
    try:
        recovery_service = PasswordRecoveryService(db)
        await recovery_service.recover_password(request.token, request.new_password)
        
        return {
            "status": "success",
            "message": "Пароль успешно восстановлен. Вы можете войти с новым паролем"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при восстановлении пароля: {str(e)}"
        )
