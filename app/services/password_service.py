from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.user import User
from app.models.user_activity import UserActivity
from app.models.auth_identity import AuthIdentity
from app.schemas.update_password_user import PasswordChangeSchema
from app.core.security.password import hash_password  


class PasswordService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def change_password_by_user_id(
        self,
        user_id: int,
        password_data: PasswordChangeSchema
    ) -> bool:
       
        stmt = select(User).options(
            selectinload(User.user_activities)
        ).where(User.user_id == user_id)
        
        result = await self.db.execute(stmt)
        user = result.scalars().first()
        
        if not user:
            raise ValueError("Пользователь не найден")
        
        if not user.user_activities:
            raise ValueError("Активность пользователя не найдена")
        
        user_activity = user.user_activities[0]
        auth_identity_id = user_activity.auth_identities_id
        
        auth_stmt = select(AuthIdentity).where(
            AuthIdentity.auth_identities_id == auth_identity_id
        )
        auth_result = await self.db.execute(auth_stmt)
        auth_identity = auth_result.scalars().first()
        
        if not auth_identity:
            raise ValueError("Запись аутентификации не найдена")
        
        hashed_password = hash_password(password_data.new_password)
        
        auth_identity.password = hashed_password
        
        await self.db.commit()
        
        return True

    async def verify_user_password(
        self,
        user_id: int,
        plain_password: str
    ) -> bool:
        
        from app.core.security.password import verify_password
        
        stmt = select(User).options(
            selectinload(User.user_activities)
        ).where(User.user_id == user_id)
        
        result = await self.db.execute(stmt)
        user = result.scalars().first()
        
        if not user or not user.user_activities:
            return False
        
        user_activity = user.user_activities[0]
        auth_identity_id = user_activity.auth_identities_id
        
        auth_stmt = select(AuthIdentity).where(
            AuthIdentity.auth_identities_id == auth_identity_id
        )
        auth_result = await self.db.execute(auth_stmt)
        auth_identity = auth_result.scalars().first()
        
        if not auth_identity or not auth_identity.password:
            return False
        
        return verify_password(plain_password, auth_identity.password)