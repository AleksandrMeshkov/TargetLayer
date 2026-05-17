from typing import List, Optional
from datetime import datetime
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.models.goal import Goal
from app.models.roadmap import Roadmap
from app.models.task import Task

logger = logging.getLogger(__name__)


async def create_roadmap_manual(
    db: AsyncSession,
    user_id: int,
    title: str,
    description: Optional[str] = None,
    tasks: Optional[List[dict]] = None,
    team_id: Optional[int] = None,
):

    try:
        logger.info(f"Создание роудмапа для пользователя {user_id}: {title}")

        new_goal = Goal(
            user_id=user_id,
            title=title,
            description=description,
            created_at=datetime.utcnow(),
        )
        db.add(new_goal)
        await db.flush()

        new_roadmap = Roadmap(
            team_id=team_id,
            goals_id=new_goal.goals_id,
            completed=False,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(new_roadmap)
        await db.flush()

        tasks_count = 0
        if tasks:
            for idx, t in enumerate(tasks):
                title_t = t.get("title")
                if not title_t:
                    continue
                description_t = t.get("description")
                order_index = t.get("order_index")
                if order_index is None:
                    order_index = idx

                new_task = Task(
                    roadmap_id=new_roadmap.roadmap_id,
                    title=title_t,
                    description=description_t,
                    order_index=order_index,
                    completed=False,
                    created_at=datetime.utcnow(),
                )
                db.add(new_task)
                tasks_count += 1

        await db.commit()
        logger.info(f"Роудмап создан: {new_roadmap.roadmap_id}, задач: {tasks_count}")

        return {"status": "success", "roadmap_id": new_roadmap.roadmap_id, "tasks": tasks_count}

    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        logger.error(f"Ошибка при создании роудмапа: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при создании роудмапа",
        )
