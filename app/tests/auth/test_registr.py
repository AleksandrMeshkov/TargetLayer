import unittest
from uuid import uuid4

from sqlalchemy import delete, select

from app.core.database.database import AsyncSessionLocal, engine
from app.models.user import User
from app.services.user.auth_service import AuthService


class AuthServiceRegisterEmailTests(unittest.IsolatedAsyncioTestCase):
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

	async def test_register_email_creates_user(self):
		unique_suffix = uuid4().hex[:8]
		username = f"test_user_{unique_suffix}"
		email = f"{username}@example.com"

		try:
			user_id = await self.service.register_email(
				username,
				email,
				"Secret123!",
				"Aleksandr",
				"Familiya",
			)
			self.created_user_id = user_id

			result = await self.db.execute(select(User).where(User.user_id == user_id))
			user = result.scalars().first()

			self.assertIsNotNone(user)
			assert user is not None
			self.assertEqual(user.user_id, user_id)
			self.assertEqual(user.username, username)
			self.assertEqual(user.email, email)
			self.assertEqual(user.name, "Aleksandr")
			self.assertEqual(user.surname, "Familiya")
			self.assertTrue(user.password_hash)
		finally:
			if self.created_user_id is not None:
				await self.db.execute(delete(User).where(User.user_id == self.created_user_id))
				await self.db.commit()
				self.created_user_id = None

	async def test_register_email_requires_username(self):
		with self.assertRaisesRegex(ValueError, "Имя пользователя обязательно"):
			await self.service.register_email(
				"   ",
				"pochta@gmail.com",
				"Secret123!",
				"Aleksandr",
				"Familiya",
			)
