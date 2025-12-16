from typing import Optional, Dict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security.password import hash_password, verify_password
from app.core.security.jwt import JWTManager
from app.models.auth_identity import AuthIdentity
from app.models.user import User
from app.models.user_activity import UserActivity
from app.models.chat_message import ChatMessage
from app.models.message import Message
from app.models.chat import Chat


class AuthService:
	def __init__(self, db: AsyncSession):
		self.db = db
		self.jwt = JWTManager()

	async def register_email(
		self, email: str, password: str, username: str, name: str, surname: str, patronymic: str | None = None
	) -> int:
		# Проверка существующего email
		q = await self.db.execute(select(AuthIdentity).where(AuthIdentity.email == email))
		existing = q.scalars().first()
		if existing:
			raise ValueError("Email already registered")

		# Создаем записи в нужных таблицах: AuthIdentity, User, Message, Chat, ChatMessage
		auth = AuthIdentity(email=email, password=hash_password(password))
		user = User(name=name, surname=surname, patronymic=patronymic)

		# создаём служебные записи для Message и Chat, чтобы ChatMessage не нарушал NOT NULL
		message = Message(content=f"Welcome message for {email}")
		chat = Chat()
		chat_msg = ChatMessage(message=message, chat=chat)

		self.db.add_all([auth, user, message, chat, chat_msg])
		await self.db.flush()

		# Создаем запись UserActivity, связывая созданные записи
		user_activity = UserActivity(
			auth_identity=auth,
			user=user,
			chat_message=chat_msg,
		)
		self.db.add(user_activity)
		await self.db.commit()
		await self.db.refresh(user_activity)

		return int(user_activity.user_activity_id)

	async def authenticate_email(self, email: str, password: str) -> Optional[int]:
		q = await self.db.execute(select(AuthIdentity).where(AuthIdentity.email == email))
		auth = q.scalars().first()
		if not auth:
			return None

		if not verify_password(password, auth.password or ""):
			return None

		# находим UserActivity для этой личности
		q2 = await self.db.execute(select(UserActivity).where(UserActivity.auth_identities_id == auth.auth_identities_id))
		ua = q2.scalars().first()
		if not ua:
			return None
		return int(ua.user_activity_id)

	async def create_tokens(self, user_activity_id: int) -> Dict[str, Optional[str]]:
		sub = str(user_activity_id)
		access = self.jwt.create_access_token(sub)
		refresh = self.jwt.create_refresh_token(sub)
		return {"access_token": access, "refresh_token": refresh, "token_type": "bearer"}

	async def refresh_tokens(self, refresh_token: str) -> Optional[Dict[str, Optional[str]]]:
		payload = self.jwt.decode_token(refresh_token)
		if not isinstance(payload, dict):
			return None
		if payload.get("type") != "refresh":
			return None
		sub = payload.get("sub")
		try:
			user_activity_id = int(sub)
		except Exception:
			return None

		# Опционально: можно дополнительно проверить, что такой user_activity существует
		q = await self.db.execute(select(UserActivity).where(UserActivity.user_activity_id == user_activity_id))
		ua = q.scalars().first()
		if not ua:
			return None

		return await self.create_tokens(user_activity_id)
