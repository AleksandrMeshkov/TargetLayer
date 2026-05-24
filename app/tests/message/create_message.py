import unittest
from uuid import uuid4

from sqlalchemy import delete, select

from app.core.database.database import AsyncSessionLocal, engine
from app.models.message import Message
from app.models.team import Team
from app.models.user import User
from app.services.chat.message_service import send_chat_message
from app.services.chat.team_chat import get_or_create_team_chat
from app.services.team_service.create_team import create_team
from app.services.team_service.delete_team import delete_team
from app.services.user.auth_service import AuthService


class TeamMessageCreationTests(unittest.IsolatedAsyncioTestCase):
	async def asyncSetUp(self):
		self.db = AsyncSessionLocal()
		self.auth_service = AuthService(self.db)
		self.created_user_id = None
		self.created_team_id = None

	async def asyncTearDown(self):
		try:
			if self.created_team_id is not None and self.created_user_id is not None:
				user_result = await self.db.execute(select(User).where(User.user_id == self.created_user_id))
				user = user_result.scalars().first()
				if user is not None:
					await delete_team(self.db, user, self.created_team_id)
			if self.created_user_id is not None:
				await self.db.execute(delete(User).where(User.user_id == self.created_user_id))
				await self.db.commit()
			elif self.created_team_id is not None:
				await self.db.commit()
			else:
				await self.db.rollback()
		finally:
			await self.db.close()
			await engine.dispose()

	async def test_create_team_message(self):
		unique_suffix = uuid4().hex[:8]
		username = f"message_user_{unique_suffix}"
		email = f"{username}@example.com"
		team_name = f"Команда {unique_suffix}"
		message_text = "Привет, команда"

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

		chat = await get_or_create_team_chat(self.db, team_id=team.team_id, user_id=user.user_id)
		message = await send_chat_message(
			self.db,
			chat_id=chat.chat_id,
			user_id=user.user_id,
			content=message_text,
		)

		message_result = await self.db.execute(select(Message).where(Message.message_id == message.message_id))
		created_message = message_result.scalars().first()

		self.assertIsNotNone(created_message)
		assert created_message is not None
		self.assertEqual(created_message.content, message_text)
		self.assertEqual(created_message.chat_id, chat.chat_id)
		self.assertEqual(created_message.user_id, user.user_id)
