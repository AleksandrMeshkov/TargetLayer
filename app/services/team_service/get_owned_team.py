from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.team import Team
from app.models.team_member import TeamMember
from app.models.team_role import TeamRole
from app.models.user import User


async def get_owned_team(db: AsyncSession, user: User, team_id: int) -> Team:
	team_stmt = select(Team).where(Team.team_id == team_id)
	team_result = await db.execute(team_stmt)
	team = team_result.scalar_one_or_none()
	if not team:
		raise HTTPException(
			status_code=status.HTTP_404_NOT_FOUND,
			detail="Team not found",
		)

	owner_stmt = (
		select(TeamMember)
		.join(TeamRole, TeamRole.team_role_id == TeamMember.team_role_id)
		.where(
			TeamMember.team_id == team_id,
			TeamMember.user_id == user.user_id,
			TeamRole.name == "Администратор",
		)
	)
	owner_result = await db.execute(owner_stmt)
	owner = owner_result.scalar_one_or_none()
	if not owner:
		raise HTTPException(
			status_code=status.HTTP_403_FORBIDDEN,
			detail="Только Администратор может управлять командой",
		)

	return team
