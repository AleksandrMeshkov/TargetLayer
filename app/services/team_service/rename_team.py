from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.team import Team
from app.models.user import User
from app.services.team_service.get_owned_team import get_owned_team


async def rename_team(db: AsyncSession, user: User, team_id: int, name: str) -> Team:
	team = await get_owned_team(db, user, team_id)

	new_name = (name or "").strip()
	if not new_name:
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail="Team name is required",
		)

	existing_stmt = select(Team).where(Team.name == new_name, Team.team_id != team_id)
	existing_result = await db.execute(existing_stmt)
	if existing_result.scalar_one_or_none():
		raise HTTPException(
			status_code=status.HTTP_409_CONFLICT,
			detail="Team with this name already exists",
		)

	team.name = new_name
	db.add(team)
	await db.commit()
	await db.refresh(team)
	return team
