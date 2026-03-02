from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException

from app.models.user import User
from app.core.security.password import hash_password
from app.core.security.jwt import JWTManager
from app.core.email.message_sender import MessageSender


class PasswordRecoveryService:
    
    def __init__(self, session: AsyncSession):
        self._session = session
        self.message_sender = MessageSender()
        self.jwt = JWTManager()

    async def create_recovery(self, email: str) -> bool:
        user = await self._get_user_by_email(email)
        if not user:
            raise HTTPException(status_code=400, detail="Пользователь с таким email не найден")

        token = self.jwt.create_recovery_token(str(user.user_id))

        email_sent = await self.message_sender.send_recovery_link(email, token)
        if not email_sent:
            raise HTTPException(status_code=400, detail="Ошибка при отправке письма восстановления")

        return True

    async def recover_password(self, token: str, new_password: str) -> bool:
        try:
            sub = self.jwt.verify_recovery_token(token)
            user_id = int(sub)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Неверный или просроченный токен: {str(e)}")

        user = await self._get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=400, detail="Пользователь не найден")

        try:
            user.password_hash = hash_password(new_password)
            self._session.add(user)
            await self._session.commit()
            return True
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
