from typing import List
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.models.roadmap import Roadmap
from app.models.goal import Goal
from app.models.task import Task


async def _verify_roadmap_owner(db: AsyncSession, user_id: int, roadmap_id: int) -> Roadmap:
    stmt = select(Roadmap).where(Roadmap.roadmap_id == roadmap_id)
    res = await db.execute(stmt)
    roadmap = res.scalars().first()
    if not roadmap:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Roadmap not found")

    goal_stmt = select(Goal).where((Goal.goals_id == roadmap.goals_id) & (Goal.user_id == user_id))
    goal_res = await db.execute(goal_stmt)
    goal = goal_res.scalars().first()
    if not goal:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You don't have access to this roadmap")

    return roadmap


async def create_task_for_roadmap(
    db: AsyncSession,
    user_id: int,
    roadmap_id: int,
    title: str,
    description: str | None = None,
    order_index: int | None = 0,
    deadline_start: datetime | None = None,
    deadline_end: datetime | None = None,
) -> Task:
    roadmap = await _verify_roadmap_owner(db, user_id, roadmap_id)

    task = Task(
        roadmap_id=roadmap.roadmap_id,
        title=title,
        description=description,
        order_index=order_index or 0,
        completed=False,
        completed_at=None,
        deadline_start=deadline_start,
        deadline_end=deadline_end,
    )
    db.add(task)
    await db.flush()
    await db.commit()
    await db.refresh(task)
    return task


async def update_task_for_roadmap(
    db: AsyncSession,
    user_id: int,
    roadmap_id: int,
    task_id: int,
    data: dict,
) -> Task:
    roadmap = await _verify_roadmap_owner(db, user_id, roadmap_id)

    stmt = select(Task).where(Task.task_id == task_id, Task.roadmap_id == roadmap.roadmap_id)
    res = await db.execute(stmt)
    task = res.scalars().first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    for key, val in data.items():
        if hasattr(task, key) and val is not None:
            setattr(task, key, val)

    if "completed" in data:
        if data.get("completed"):
            task.completed_at = datetime.utcnow()
        else:
            task.completed_at = None

    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task


async def delete_task_for_roadmap(
    db: AsyncSession,
    user_id: int,
    roadmap_id: int,
    task_id: int,
) -> None:
    roadmap = await _verify_roadmap_owner(db, user_id, roadmap_id)

    stmt = select(Task).where(Task.task_id == task_id, Task.roadmap_id == roadmap.roadmap_id)
    res = await db.execute(stmt)
    task = res.scalars().first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    await db.delete(task)
    await db.commit()


async def set_task_complete_for_roadmap(
    db: AsyncSession,
    user_id: int,
    roadmap_id: int,
    task_id: int,
    completed: bool,
) -> Task:
    roadmap = await _verify_roadmap_owner(db, user_id, roadmap_id)

    stmt = select(Task).where(Task.task_id == task_id, Task.roadmap_id == roadmap.roadmap_id)
    res = await db.execute(stmt)
    task = res.scalars().first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    task.completed = bool(completed)
    task.completed_at = datetime.utcnow() if completed else None

    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task
