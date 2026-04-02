from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status
from app.models.roadmap import Roadmap
from app.models.goal import Goal
from app.models.task import Task
from app.models.roadmap_copy import RoadmapCopy
from datetime import datetime

async def copy_roadmap(db: AsyncSession, user_id: int, roadmap_id: int):
	orig_roadmap = await db.get(Roadmap, roadmap_id)
	if not orig_roadmap:
		raise HTTPException(status_code=404, detail="Оригинальный роудмап не найден")

	orig_goal = orig_roadmap.goal
	if not orig_goal:
		raise HTTPException(status_code=404, detail="Goal не найден")

	new_goal = Goal(
		user_id=user_id,
		title=orig_goal.title,
		description=orig_goal.description,
		created_at=datetime.utcnow()
	)
	db.add(new_goal)
	await db.flush()

	new_roadmap = Roadmap(
		team_id=None,
		goals_id=new_goal.goals_id,
		completed=False,
		created_at=datetime.utcnow(),
		updated_at=datetime.utcnow()
	)
	db.add(new_roadmap)
	await db.flush()

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

	roadmap_copy = RoadmapCopy(
		user_id=user_id,
		original_roadmap_id=roadmap_id,
		new_roadmap_id=new_roadmap.roadmap_id,
		created_at=datetime.utcnow()
	)
	db.add(roadmap_copy)
	await db.commit()
	return {"status": "success", "new_roadmap_id": new_roadmap.roadmap_id}
