from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User
from app.schemas.update_password_user import PasswordChangeSchema
from app.core.security.password import hash_password, verify_password


class PasswordService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def change_password_by_user_id(
        self,
        user_id: int,
        password_data: PasswordChangeSchema
    ) -> bool:
       
        stmt = select(User).where(User.user_id == user_id)
        
        result = await self.db.execute(stmt)
        user = result.scalars().first()
        
        if not user:
            raise ValueError("Пользователь не найден")

        if not user.password_hash or not verify_password(password_data.old_password, user.password_hash):
            raise ValueError("Старый пароль указан неверно")
        
        hashed_password = hash_password(password_data.new_password)
        
        user.password_hash = hashed_password
        
        await self.db.commit()
        
        return True

    async def verify_user_password(
        self,
        user_id: int,
        plain_password: str
    ) -> bool:
        stmt = select(User).where(User.user_id == user_id)
        
        result = await self.db.execute(stmt)
        user = result.scalars().first()
        
        if not user or not user.password_hash:
            return False
        
        return verify_password(plain_password, user.password_hash)