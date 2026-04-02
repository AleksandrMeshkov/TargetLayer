from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.team_member import TeamMember
from app.models.user import User
from app.services.team_service.get_or_create_team_role import get_or_create_team_role
from app.services.team_service.get_owned_team import get_owned_team


async def update_team_member_role(
	db: AsyncSession,
	current_user: User,
	team_id: int,
	target_user_id: int,
	new_role_name: str,
) -> TeamMember:
	# Only team admin can change roles
	await get_owned_team(db, current_user, team_id)

	stmt = select(TeamMember).where(
		TeamMember.team_id == team_id,
		TeamMember.user_id == target_user_id,
	)
	res = await db.execute(stmt)
	membership = res.scalar_one_or_none()
	if not membership:
		raise HTTPException(
			status_code=status.HTTP_404_NOT_FOUND,
			detail="User is not a member of this team",
		)

	role = await get_or_create_team_role(db, new_role_name)
	membership.team_role_id = role.team_role_id
	
	db.add(membership)
	await db.commit()
	await db.refresh(membership)
	return membership
