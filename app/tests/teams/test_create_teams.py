import unittest
from uuid import uuid4

from sqlalchemy import delete, select

from app.core.database.database import AsyncSessionLocal, engine
from app.models.team import Team
from app.models.user import User
from app.services.team_service.create_team import create_team
from app.services.user.auth_service import AuthService


class TeamCreationTests(unittest.IsolatedAsyncioTestCase):
	async def asyncSetUp(self):
		self.db = AsyncSessionLocal()
		self.auth_service = AuthService(self.db)
		self.created_user_id = None
		self.created_team_id = None

	async def asyncTearDown(self):
		try:
			if self.created_team_id is not None:
				await self.db.execute(delete(Team).where(Team.team_id == self.created_team_id))
			if self.created_user_id is not None:
				await self.db.execute(delete(User).where(User.user_id == self.created_user_id))
			if self.created_team_id is not None or self.created_user_id is not None:
				await self.db.commit()
			else:
				await self.db.rollback()
		finally:
			await self.db.close()
			await engine.dispose()

	async def test_create_team(self):
		unique_suffix = uuid4().hex[:8]
		username = f"team_user_{unique_suffix}"
		email = f"{username}@example.com"
		team_name = f"Команда {unique_suffix}"

		user_id = await self.auth_service.register_email(
			username,
			email,
			"Secret123!",
			"Александр",
			"Иванов",
		)
		self.created_user_id = user_id

		user_result = await self.db.execute(select(User).where(User.user_id == user_id))
		user = user_result.scalars().first()
		self.assertIsNotNone(user)
		assert user is not None

		team = await create_team(self.db, user, team_name)
		self.created_team_id = team.team_id

		team_result = await self.db.execute(select(Team).where(Team.team_id == team.team_id))
		created_team = team_result.scalars().first()

		self.assertIsNotNone(created_team)
		assert created_team is not None
		self.assertEqual(created_team.name, team_name)
