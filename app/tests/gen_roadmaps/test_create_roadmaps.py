import unittest
from uuid import uuid4
from unittest.mock import AsyncMock, patch

from sqlalchemy import delete, select
from sqlalchemy.orm import selectinload

from app.api.v1.ai.ai_router import ai_chat
from app.core.database.database import AsyncSessionLocal, engine
from app.models.goal import Goal
from app.models.roadmap import Roadmap
from app.models.task import Task
from app.models.user import User
from app.schemas.ai_schemas import AIRoadmapRequest
from app.services.user.auth_service import AuthService


class AIroadmapGenerationTests(unittest.IsolatedAsyncioTestCase):
	async def asyncSetUp(self):
		self.db = AsyncSessionLocal()
		self.auth_service = AuthService(self.db)
		self.created_user_id = None
		self.created_roadmap_id = None

	async def asyncTearDown(self):
		try:
			if self.created_roadmap_id is not None:
				await self.db.execute(delete(Roadmap).where(Roadmap.roadmap_id == self.created_roadmap_id))
			if self.created_user_id is not None:
				await self.db.execute(delete(User).where(User.user_id == self.created_user_id))
			if self.created_roadmap_id is not None or self.created_user_id is not None:
				await self.db.commit()
			else:
				await self.db.rollback()
		finally:
			await self.db.close()
			await engine.dispose()

	async def test_generate_roadmap_waits_for_ai_and_saves_to_db(self):
		unique_suffix = uuid4().hex[:8]
		username = f"roadmap_user_{unique_suffix}"
		email = f"{username}@example.com"
		user_id = await self.auth_service.register_email(
			username,
			email,
			"Secret123!",
			"Aleksandr",
			"Aleksandrov",
		)
		self.created_user_id = user_id

		user_result = await self.db.execute(select(User).where(User.user_id == user_id))
		current_user = user_result.scalars().first()
		self.assertIsNotNone(current_user)
		assert current_user is not None

		aireturn = {
			"goal_title": "Изучить Python за 2 недели",
			"goal_description": "Короткий практический план обучения.",
			"tasks": [
				{
					"title": "Освоить основы языка",
					"description": "Пройти синтаксис и написать несколько мини-скриптов.",
					"order_index": 0,
					"deadline_offset_days": 7,
				},
			],
		}

		with patch(
			"app.api.v1.ai.ai_router.ai_service.chat",
			new=AsyncMock(return_value=aireturn),
		):
			response = await ai_chat(
				AIRoadmapRequest(prompt="Сделай короткий план изучения Python на 2 недели"),
				current_user=current_user,
				db=self.db,
			)

		self.assertEqual(response.goal_title, aireturn["goal_title"])
		self.assertEqual(len(response.tasks), 1)

		roadmap_result = await self.db.execute(
			select(Roadmap)
			.join(Goal)
			.where(Goal.user_id == user_id)
			.options(selectinload(Roadmap.goal), selectinload(Roadmap.tasks))
			.order_by(Roadmap.roadmap_id.desc())
		)
		roadmap = roadmap_result.scalars().first()

		self.assertIsNotNone(roadmap)
		assert roadmap is not None
		self.created_roadmap_id = roadmap.roadmap_id
		self.assertEqual(roadmap.goal.title, aireturn["goal_title"])
		self.assertEqual(len(roadmap.tasks), 1)
		self.assertEqual(roadmap.tasks[0].title, aireturn["tasks"][0]["title"])
