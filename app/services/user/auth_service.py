from typing import Optional, Dict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security.password import hash_password, verify_password
from app.core.security.jwt import JWTManager
from app.models.user import User
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

		user = User(
			name=name, 
			surname=surname, 
			patronymic=patronymic,
			email=email,
			password_hash=hash_password(password)
		)
		self.db.add(user)
		await self.db.flush()

		goal = Goal(
			user_id=user.user_id,
			title="Default Goal", 
			description="Default goal for new user"
		)
		self.db.add(goal)
		await self.db.flush()

		roadmap = Roadmap(
			goals_id=goal.goals_id,
			completed=False
		)
		self.db.add(roadmap)
		await self.db.flush()

		task = Task(
			roadmap_id=roadmap.roadmap_id,
			title="Default Task",
			description="Default task for new user"
		)
		self.db.add(task)
		await self.db.flush()

		chat = Chat()
		self.db.add(chat)
		await self.db.flush()

		message = Message(
			content=f"Welcome message for {email}",
			user_id=user.user_id,
			chat_id=chat.chat_id
		)
		self.db.add(message)
		await self.db.commit()
		await self.db.refresh(user)

		return int(user.user_id)

	async def authenticate_email(self, email: str, password: str) -> Optional[int]:
		q = await self.db.execute(select(User).where(User.email == email))
		user = q.scalars().first()
		if not user:
			return None

		if not verify_password(password, user.password_hash or ""):
			return None

		return int(user.user_id)

	async def create_tokens(self, user_id: int) -> Dict[str, Optional[str]]:
		sub = str(user_id)
		access = self.jwt.create_access_token(sub)
		refresh = self.jwt.create_refresh_token(sub)
		return {"access_token": access, "refresh_token": refresh, "token_type": "bearer"}

	async def refresh_tokens(self, refresh_token: str) -> Optional[Dict[str, Optional[str]]]:
		
		try:
			access, refresh = self.jwt.rotate_tokens(refresh_token)
			return {"access_token": access, "refresh_token": refresh, "token_type": "bearer"}
		except Exception:  
			return None
