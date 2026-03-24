import asyncio
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database.database import get_db
from app.schemas.password_recovery import (
    PasswordRecoveryRequestSchema,
    PasswordRecoveryConfirmSchema,
    PasswordRecoveryResponseSchema
)
from app.services.password.password_recovery_service import PasswordRecoveryService

router = APIRouter(prefix="/api/v1/password", tags=["password-recovery"])

RECOVERY_COOLDOWN_SECONDS = 60
_last_recovery_requests: dict[str, datetime] = {}
_recovery_requests_lock = asyncio.Lock()


async def _reserve_recovery_request(email: str) -> None:
    normalized_email = email.strip().lower()
    now = datetime.now(timezone.utc)

    async with _recovery_requests_lock:
        last_request_at = _last_recovery_requests.get(normalized_email)
        if last_request_at:
            elapsed = now - last_request_at
            if elapsed < timedelta(seconds=RECOVERY_COOLDOWN_SECONDS):
                retry_after = int((timedelta(seconds=RECOVERY_COOLDOWN_SECONDS) - elapsed).total_seconds()) + 1
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Слишком частый запрос. Повторите через {retry_after} сек.",
                    headers={"Retry-After": str(retry_after)},
                )

        _last_recovery_requests[normalized_email] = now


async def _rollback_recovery_reservation(email: str) -> None:
    normalized_email = email.strip().lower()
    async with _recovery_requests_lock:
        _last_recovery_requests.pop(normalized_email, None)


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
    reservation_created = False

    try:
        await _reserve_recovery_request(request.email)
        reservation_created = True
        recovery_service = PasswordRecoveryService(db)
        await recovery_service.create_recovery(request.email)

        return PasswordRecoveryResponseSchema(
            status="success",
            message="Письмо с ссылкой восстановления отправлено на вашу почту",
            email=request.email,
        )
    except HTTPException:
        if reservation_created:
            await _rollback_recovery_reservation(request.email)
        raise
    except Exception as e:
        if reservation_created:
            await _rollback_recovery_reservation(request.email)
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
