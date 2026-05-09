from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status
from app.models.roadmap import Roadmap
from app.models.goal import Goal
from app.models.task import Task
from app.models.roadmap_copy import RoadmapCopy
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

async def copy_roadmap(db: AsyncSession, user_id: int, roadmap_id: int):
	
	try:
		logger.info(f"Начало копирования роудмапа {roadmap_id} для пользователя {user_id}")
		
		stmt = (
			select(Roadmap)
			.where(Roadmap.roadmap_id == roadmap_id)
			.options(selectinload(Roadmap.goal), selectinload(Roadmap.tasks))
		)
		result = await db.execute(stmt)
		orig_roadmap = result.unique().scalar_one_or_none()
		
		if not orig_roadmap:
			logger.warning(f"Роудмап {roadmap_id} не найден")
			raise HTTPException(status_code=404, detail="Оригинальный роудмап не найден")
		
		logger.info(f"Роудмап найден: {orig_roadmap.roadmap_id}")
		
		orig_goal = orig_roadmap.goal
		if not orig_goal:
			logger.error(f"Goal не найден для роудмапа {roadmap_id}")
			raise HTTPException(status_code=400, detail="У оригинального роудмапа отсутствует цель")
		
		logger.info(f"Goal найдена: {orig_goal.goals_id}, title: {orig_goal.title}")
		
		new_goal = Goal(
			user_id=user_id,
			title=orig_goal.title,
			description=orig_goal.description,
			created_at=datetime.utcnow()
		)
		db.add(new_goal)
		await db.flush()
		logger.info(f"Новая goal создана: {new_goal.goals_id}")
		
		new_roadmap = Roadmap(
			team_id=None,
			goals_id=new_goal.goals_id,
			completed=False,
			created_at=datetime.utcnow(),
			updated_at=datetime.utcnow()
		)
		db.add(new_roadmap)
		await db.flush()
		logger.info(f"Новый роудмап создан: {new_roadmap.roadmap_id}")
		
		tasks_count = 0
		if orig_roadmap.tasks:
			for orig_task in orig_roadmap.tasks:
				new_task = Task(
					roadmap_id=new_roadmap.roadmap_id,
					title=orig_task.title,
					description=orig_task.description,
					order_index=orig_task.order_index,
					completed=False,
					created_at=datetime.utcnow()
				)
				db.add(new_task)
				tasks_count += 1
			logger.info(f"Скопировано {tasks_count} задач")
		else:
			logger.info("У оригинального роудмапа нет задач")
		
		roadmap_copy = RoadmapCopy(
			user_id=user_id,
			original_roadmap_id=roadmap_id,
			new_roadmap_id=new_roadmap.roadmap_id,
			created_at=datetime.utcnow()
		)
		db.add(roadmap_copy)
		
		await db.commit()
		logger.info(f"Роудмап успешно скопирован: {roadmap_id} -> {new_roadmap.roadmap_id}")
		
		return {"status": "success", "new_roadmap_id": new_roadmap.roadmap_id}
		
	except HTTPException:
		await db.rollback()
		raise
	except Exception as e:
		logger.error(f"Ошибка при копировании роудмапа {roadmap_id}: {str(e)}", exc_info=True)
		await db.rollback()
		raise HTTPException(
			status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
			detail=f"Ошибка при копировании роудмапа: {str(e)}"
		)
