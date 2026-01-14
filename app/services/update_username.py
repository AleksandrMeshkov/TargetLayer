from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.models.user import User
from app.schemas.update_user import UserNameSchema


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def update_user_name(
        self, 
        user_id: int, 
        name_data: UserNameSchema
    ) -> User:
        stmt = select(User).where(User.user_id == user_id)
        result = await self.db.execute(stmt)
        user = result.scalars().first()
        
        if not user:
            raise ValueError("User not found")
        
        user.name = name_data.name
        user.surname = name_data.surname
        user.patronymic = name_data.patronymic
        
        await self.db.commit()
        await self.db.refresh(user)
        
        return user

    async def get_user_profile(self, user_id: int) -> Optional[User]:
        stmt = select(User).where(User.user_id == user_id)
        result = await self.db.execute(stmt)
        return result.scalars().first()