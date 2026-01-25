from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.services.user.email_service import EmailVerificationService
from app.core.database.database import get_db
from app.models.user import User
from app.models.user_activity import UserActivity

router = APIRouter(prefix="/verify", tags=["verification"])


@router.post("/send-code")
async def send_code(
    email: str = Query(..., description="Email адрес для отправки кода"),
    db: AsyncSession = Depends(get_db)
):
    
    result = await db.execute(
        select(User).where(User.email == email)
    )
    user = result.scalars().first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email не найден в системе"
        )
    
    email_service = EmailVerificationService()
    if await email_service.is_verification_pending(email):
        ttl = await email_service.get_remaining_ttl(email)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Код уже отправлен. Повторите попытку через {ttl} секунд"
        )
    
    try:
        code = await email_service.send_verification_code(email)
        
        return {
            "status": "success",
            "message": "Код подтверждения отправлен на email",
            "email": email
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при отправке кода: {str(e)}"
        )


@router.post("/confirm")
async def confirm_email(
    email: str = Query(..., description="Email адрес"),
    code: str = Query(..., description="Код подтверждения из письма"),
    db: AsyncSession = Depends(get_db)
):
    email_service = EmailVerificationService()

    is_valid = await email_service.verify_code(email, code)
    
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Неверный или истёкший код подтверждения"
        )
    
    result = await db.execute(
        select(User).where(User.email == email)
    )
    user = result.scalars().first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    
    try:
        user.email_verified = True
        db.add(user)
        await db.commit()
        
        return {
            "status": "success",
            "message": "Email успешно подтвержден",
            "email": email,
            "user_id": user.user_id
        }
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при обновлении статуса верификации: {str(e)}"
        )