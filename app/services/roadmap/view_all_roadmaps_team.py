from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.roadmap import Roadmap

async def get_team_roadmaps(db: AsyncSession, team_id: int) -> list[Roadmap]:
	stmt = (
		select(Roadmap)
		.options(selectinload(Roadmap.tasks), selectinload(Roadmap.goal))
		.where(Roadmap.team_id == team_id)
		.order_by(Roadmap.updated_at.desc())
	)
	result = await db.execute(stmt)
	return list(result.scalars().all())
