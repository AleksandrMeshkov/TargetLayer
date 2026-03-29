from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.team import Team
from app.models.team_member import TeamMember
from app.models.user import User


async def get_user_teams(db: AsyncSession, user: User) -> list[Team]:
	stmt = (
		select(Team)
		.join(TeamMember, TeamMember.team_id == Team.team_id)
		.where(TeamMember.user_id == user.user_id)
		.order_by(Team.created_at.desc())
	)
	result = await db.execute(stmt)
	return list(result.scalars().unique().all())
