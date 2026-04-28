from typing import Optional, Dict
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security.password import hash_password, verify_password
from app.core.security.jwt import JWTManager
from app.models.user import User
from app.models.message import Message
from app.models.chat import Chat
from app.models.chat_participant import ChatParticipant
from app.models.team import Team
from app.models.team_role import TeamRole
from app.models.team_member import TeamMember
from app.models.roadmap import Roadmap
from app.models.goal import Goal
from app.models.roadmap_access import RoadmapAccess
from app.models.task import Task


class AuthService:
	def __init__(self, db: AsyncSession):
		self.db = db
		self.jwt = JWTManager()

	async def register_email(
		self,
		username: str,
		email: str,
		password: str,
		name: str,
		surname: str,
		patronymic: str | None = None,
	) -> int:
		normalized_username = (username or "").strip()
		normalized_email = (email or "").strip().lower()
		if not normalized_username:
			raise ValueError("Username is required")
		if not normalized_email:
			raise ValueError("Email is required")

		username_q = await self.db.execute(
			select(User).where(func.lower(User.username) == normalized_username.lower())
		)
		existing_username = username_q.scalars().first()
		if existing_username:
			if (
				existing_username.email.lower() == normalized_email
				and verify_password(password, existing_username.password_hash or "")
			):
				return int(existing_username.user_id)
			raise ValueError("Username already taken")

		q = await self.db.execute(select(User).where(func.lower(User.email) == normalized_email))
		existing = q.scalars().first()
		if existing:
			if (
				existing.username.lower() == normalized_username.lower()
				and verify_password(password, existing.password_hash or "")
			):
				return int(existing.user_id)
			raise ValueError("Email already registered")

		user = User(
			username=normalized_username,
			name=name, 
			surname=surname, 
			patronymic=patronymic,
			email=normalized_email,
			password_hash=hash_password(password)
		)
		self.db.add(user)
		await self.db.flush()

		# Создаём роль 'Администратор', если её нет
		owner_role_stmt = select(TeamRole).where(TeamRole.name == "Администратор")
		owner_role_result = await self.db.execute(owner_role_stmt)
		owner_role = owner_role_result.scalar_one_or_none()
		if owner_role is None:
			owner_role = TeamRole(name="Администратор")
			self.db.add(owner_role)
			await self.db.flush()

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
