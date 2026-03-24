from typing import Optional
from uuid import uuid4

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.settings.settings import settings
from app.models.user import User
from app.schemas.update_user import UserNameSchema


ALLOWED_AVATAR_CONTENT_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
}
MAX_AVATAR_SIZE_BYTES = 5 * 1024 * 1024


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

    async def update_user_avatar(
        self,
        user_id: int,
        avatar_file: UploadFile
    ) -> User:
        stmt = select(User).where(User.user_id == user_id)
        result = await self.db.execute(stmt)
        user = result.scalars().first()
        
        if not user:
            raise ValueError("Пользователь не найден")

        file_extension = ALLOWED_AVATAR_CONTENT_TYPES.get(avatar_file.content_type or "")
        if not file_extension:
            raise ValueError("Недопустимый формат изображения. Разрешены: jpg, png, webp, gif")

        file_bytes = await avatar_file.read()
        if not file_bytes:
            raise ValueError("Файл изображения пуст")
        if len(file_bytes) > MAX_AVATAR_SIZE_BYTES:
            raise ValueError("Файл слишком большой. Максимальный размер: 5 MB")

        file_name = f"user_{user_id}_{uuid4().hex}{file_extension}"
        file_path = settings.avatars_dir_path / file_name
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_bytes(file_bytes)

        user.avatar_url = (
            f"{settings.server_base_url}{settings.UPLOADS_URL_PREFIX}/avatars/{file_name}"
        )
        
        await self.db.commit()
        await self.db.refresh(user)

        return user

    async def get_user_profile(self, user_id: int) -> Optional[User]:
        stmt = select(User).where(User.user_id == user_id)
        result = await self.db.execute(stmt)
        return result.scalars().first()