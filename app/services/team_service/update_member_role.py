from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.team_member import TeamMember
from app.models.team_role import TeamRole
from app.models.user import User
from app.services.team_service.get_owned_team import get_owned_team


async def update_team_member_role(
	db: AsyncSession,
	current_user: User,
	team_id: int,
	target_user_id: int,
	role_id: int,
) -> TeamMember:
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
			detail="Пользователь не является членом этой команды",
		)

	role_stmt = select(TeamRole).where(TeamRole.team_role_id == role_id)
	role_res = await db.execute(role_stmt)
	role = role_res.scalar_one_or_none()
	if not role:
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail=f"Роль с ID {role_id} не найдена",
		)

	membership.team_role_id = role_id
	
	db.add(membership)
	await db.commit()
	await db.refresh(membership)
	return membership
