import random
import string
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException

from app.models.password_recovery import PasswordRecovery
from app.models.user import User
from app.core.security.password import hash_password
from app.core.email.message_sender import MessageSender


class PasswordRecoveryService:
    
    TOKEN_LENGTH = 64
    TOKEN_EXPIRY_HOURS = 24
    
    def __init__(self, session: AsyncSession):
        self._session = session
        self.message_sender = MessageSender()
    
    def _generate_recovery_token(self) -> str:
        
        characters = string.ascii_letters + string.digits
        return "".join(random.choice(characters) for _ in range(self.TOKEN_LENGTH))
    
    async def create_recovery(self, email: str) -> PasswordRecovery:
        
        user = await self._get_user_by_email(email)
        if not user:
            raise HTTPException(status_code=400, detail="Пользователь с таким email не найден")
        
        token = self._generate_recovery_token()
        
        expires_at = datetime.now(timezone.utc) + timedelta(hours=self.TOKEN_EXPIRY_HOURS)
        
        try:
            recovery = PasswordRecovery(
                user_id=user.user_id,
                token=token,
                expires_at=expires_at
            )
            self._session.add(recovery)
            await self._session.commit()
            await self._session.refresh(recovery)
        except Exception as e:
            await self._session.rollback()
            raise HTTPException(status_code=400, detail=f"Ошибка при создании запроса восстановления: {str(e)}")
        
        email_sent = await self.message_sender.send_recovery_link(email, token)
        if not email_sent:
            raise HTTPException(status_code=400, detail="Ошибка при отправке письма восстановления")
        
        return recovery
    
    async def recover_password(self, token: str, new_password: str) -> bool:
        
        recovery = await self._get_recovery_by_token(token)
        if not recovery:
            raise HTTPException(status_code=400, detail="Токен восстановления не найден")
        
        if recovery.is_used:
            raise HTTPException(status_code=400, detail="Этот токен уже был использован")
        
        if recovery.expires_at and datetime.now(timezone.utc) > recovery.expires_at:
            raise HTTPException(status_code=400, detail="Токен восстановления истек. Запросите новый")
        
        try:
            user = await self._get_user_by_id(recovery.user_id)
            if not user:
                raise HTTPException(status_code=400, detail="Пользователь не найден")
            
            user.password = hash_password(new_password)
            
            recovery.is_used = True
            
            self._session.add(user)
            self._session.add(recovery)
            await self._session.commit()
            
            return True
        except HTTPException:
            await self._session.rollback()
            raise
        except Exception as e:
            await self._session.rollback()
            raise HTTPException(status_code=400, detail=f"Ошибка при восстановлении пароля: {str(e)}")
    
    async def _get_user_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email)
        result = await self._session.execute(stmt)
        return result.scalars().first()
    
    async def _get_user_by_id(self, user_id: int) -> User | None:
        stmt = select(User).where(User.user_id == user_id)
        result = await self._session.execute(stmt)
        return result.scalars().first()
    
    async def _get_recovery_by_token(self, token: str) -> PasswordRecovery | None:
        stmt = select(PasswordRecovery).where(PasswordRecovery.token == token)
        result = await self._session.execute(stmt)
        return result.scalars().first()
    async def _get_recovery_by_token(self, token: str) -> PasswordRecovery | None:
        stmt = select(PasswordRecovery).where(PasswordRecovery.token == token)
        result = await self._session.execute(stmt)
        return result.scalars().first()
