from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.core.security.password import hash_password, verify_password
from app.core.security.jwt import JWTManager
from app.models.user import User
from app.models.user_activity import UserActivity
from app.models.auth_identity import AuthIdentity
from app.models.provider import Provider
from datetime import datetime, timezone

class AuthService:

    def __init__(self, db: AsyncSession):
        self.db = db
        self.jwt = JWTManager()

    async def register_email(
        self,
        email: str,
        password: str,
        username: str,
        name: str,
        surname: str,
        patronymic: str | None = None
    ) -> str:
        # 1. Проверка уникальности email
        existing = await self.db.execute(
            select(AuthIdentity).where(AuthIdentity.email == email)
        )
        if existing.scalar_one_or_none():
            raise ValueError("Email already registered")

        # 2. Получение провайдера 'email'
        provider = await self.db.execute(
            select(Provider).where(Provider.name == "email")
        )
        provider = provider.scalar_one_or_none()
        if not provider:
            raise RuntimeError("Email provider not configured")

        # 3. Создание пользователя
        now = datetime.now(timezone.utc)
        user = User(
            username=username,
            name=name,
            surname=surname,
            patronymic=patronymic,
            email_verified=False,
            avatar_url=None,
            created_at=now,
            updated_at=now
        )
        self.db.add(user)
        await self.db.flush()  # Получаем user_id

        # 4. Создание активности
        activity = UserActivity(
            user_id=user.user_id,
            created_at=now
        )
        self.db.add(activity)
        await self.db.flush()  # Получаем user_activity_id
        
        # Сохраняем ID до коммита
        activity_id = activity.user_activity_id

        # 5. Создание идентификации
        auth = AuthIdentity(
            user_activity_id=activity_id,
            provider_id=provider.provider_id,
            email=email,
            password_hash=hash_password(password),
            created_at=now
        )
        self.db.add(auth)
        await self.db.commit()

        return str(activity_id)

    async def authenticate_email(self, email: str, password: str) -> str | None:
        result = await self.db.execute(
            select(AuthIdentity)
            .join(Provider)
            .where(
                AuthIdentity.email == email,
                Provider.name == "email"
            )
        )
        auth = result.scalar_one_or_none()
        if not auth or not verify_password(password, auth.password_hash):
            return None
        return str(auth.user_activity_id)

    async def create_tokens(self, user_activity_id: str) -> dict:
        return {
            "access_token": self.jwt.create_access_token(user_activity_id),
            "refresh_token": self.jwt.create_refresh_token(user_activity_id),
            "token_type": "bearer"
        }

    async def refresh_tokens(self, refresh_token: str) -> dict | None:
        payload = self.jwt.decode_token(refresh_token)
        if isinstance(payload, str) or payload.get("type") != "refresh":
            return None
        return await self.create_tokens(payload["sub"])