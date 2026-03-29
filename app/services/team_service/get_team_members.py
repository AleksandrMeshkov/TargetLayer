from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.team import Team
from app.models.team_member import TeamMember
from app.models.user import User


async def get_team_members(db: AsyncSession, user: User, team_id: int) -> list[dict]:
	team_stmt = select(Team).where(Team.team_id == team_id)
	team_result = await db.execute(team_stmt)
	team = team_result.scalar_one_or_none()
	if not team:
		raise HTTPException(
			status_code=status.HTTP_404_NOT_FOUND,
			detail="Team not found",
		)

	access_stmt = select(TeamMember).where(
		TeamMember.team_id == team_id,
		TeamMember.user_id == user.user_id,
	)
	access_result = await db.execute(access_stmt)
	membership = access_result.scalar_one_or_none()
	if not membership:
		raise HTTPException(
			status_code=status.HTTP_403_FORBIDDEN,
			detail="You do not have access to this team",
		)

	members_stmt = (
		select(
			TeamMember.id,
			TeamMember.team_id,
			TeamMember.user_id,
			TeamMember.team_role_id,
			TeamMember.joined_at,
		)
		.where(TeamMember.team_id == team_id)
		.order_by(TeamMember.joined_at.asc(), TeamMember.id.asc())
	)
	members_result = await db.execute(members_stmt)
	return [dict(row) for row in members_result.mappings().all()]
