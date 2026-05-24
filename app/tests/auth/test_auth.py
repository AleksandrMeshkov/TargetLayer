import unittest
from uuid import uuid4

from sqlalchemy import delete, select

from app.core.database.database import AsyncSessionLocal, engine
from app.models.user import User
from app.services.user.auth_service import AuthService


class AuthServiceLoginTests(unittest.IsolatedAsyncioTestCase):
	async def asyncSetUp(self):
		self.db = AsyncSessionLocal()
		self.service = AuthService(self.db)
		self.created_user_id = None

	async def asyncTearDown(self):
		try:
			if self.created_user_id is not None:
				await self.db.execute(delete(User).where(User.user_id == self.created_user_id))
				await self.db.commit()
			else:
				await self.db.rollback()
		finally:
			await self.db.close()
			await engine.dispose()

	async def test_login_with_existing_user(self):
		unique_suffix = uuid4().hex[:8]
		username = f"login_user_{unique_suffix}"
		email = f"{username}@example.com"
		password = "Secret123!"

		try:
			created_user_id = await self.service.register_email(
				username,
				email,
				password,
				"Aleksandr",
				"Aleksandrov",
			)
			self.created_user_id = created_user_id

			result = await self.db.execute(select(User).where(User.user_id == created_user_id))
			user = result.scalars().first()

			self.assertIsNotNone(user)
			assert user is not None
			self.assertEqual(user.email, email)

			authenticated_user_id = await self.service.authenticate_email(email, password)
			self.assertEqual(authenticated_user_id, created_user_id)
		finally:
			if self.created_user_id is not None:
				await self.db.execute(delete(User).where(User.user_id == self.created_user_id))
				await self.db.commit()
				self.created_user_id = None
