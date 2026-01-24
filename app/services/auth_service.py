from typing import Optional, Dict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security.password import hash_password, verify_password
from app.core.security.jwt import JWTManager
from app.models.user import User
from app.models.user_activity import UserActivity
from app.models.chat_message import ChatMessage
from app.models.message import Message
from app.models.chat import Chat
from app.models.roadmap import Roadmap
from app.models.goal import Goal
from app.models.task import Task


class AuthService:
	def __init__(self, db: AsyncSession):
		self.db = db
		self.jwt = JWTManager()

	async def register_email(
		self, email: str, password: str, username: str, name: str, surname: str, patronymic: str | None = None
	) -> int:
		q = await self.db.execute(select(User).where(User.email == email))
		existing = q.scalars().first()
		if existing:
			raise ValueError("Email already registered")

		# Step 1: Create user
		user = User(
			name=name, 
			surname=surname, 
			patronymic=patronymic,
			email=email,
			password=hash_password(password)
		)
		self.db.add(user)
		await self.db.flush()

		# Step 2: Create default goal and task
		goal = Goal(title="Default Goal", description="Default goal for new user")
		task = Task(title="Default Task", description="Default task for new user")
		self.db.add_all([goal, task])
		await self.db.flush()

		# Step 3: Create roadmap
		roadmap = Roadmap(
			goals_id=goal.goals_id,
			tasks_id=task.task_id,
			completed=False
		)
		self.db.add(roadmap)
		await self.db.flush()

		# Step 4: Create user_activity with user and roadmap
		user_activity = UserActivity(
			user_id=user.user_id,
			roadmap_id=roadmap.roadmap_id,
		)
		self.db.add(user_activity)
		await self.db.flush()

		# Step 5: Create chat and message (now that we have user_activity)
		message = Message(content=f"Welcome message for {email}")
		chat = Chat()
		self.db.add_all([message, chat])
		await self.db.flush()

		# Step 6: Create chat_message with user_activity_id
		chat_msg = ChatMessage(
			message_id=message.messages_id,
			chat_id=chat.chat_id,
			user_activity_id=user_activity.user_activity_id
		)
		self.db.add(chat_msg)
		await self.db.commit()
		await self.db.refresh(user_activity)

		return int(user_activity.user_activity_id)

	async def authenticate_email(self, email: str, password: str) -> Optional[int]:
		q = await self.db.execute(select(User).where(User.email == email))
		user = q.scalars().first()
		if not user:
			return None

		if not verify_password(password, user.password or ""):
			return None

		q2 = await self.db.execute(select(UserActivity).where(UserActivity.user_id == user.user_id))
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

		q = await self.db.execute(select(UserActivity).where(UserActivity.user_activity_id == user_activity_id))
		ua = q.scalars().first()
		if not ua:
			return None

		return await self.create_tokens(user_activity_id)
