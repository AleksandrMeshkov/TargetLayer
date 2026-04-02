from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.team import Team
from app.models.team_member import TeamMember
from app.models.user import User
from app.services.team_service.get_or_create_team_role import get_or_create_team_role


async def create_team(db: AsyncSession, user: User, name: str) -> Team:
	team_name = (name or "").strip()
	if not team_name:
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail="Team name is required",
		)

	existing_stmt = select(Team).where(Team.name == team_name)
	existing_result = await db.execute(existing_stmt)
	if existing_result.scalar_one_or_none():
		raise HTTPException(
			status_code=status.HTTP_409_CONFLICT,
			detail="Team with this name already exists",
		)

	team = Team(name=team_name)
	db.add(team)
	await db.flush()

	admin_role = await get_or_create_team_role(db, "Администратор")
	owner_membership = TeamMember(
		team_id=team.team_id,
		user_id=user.user_id,
		team_role_id=admin_role.team_role_id,
	)
	db.add(owner_membership)
	await db.commit()
	await db.refresh(team)
	return team
