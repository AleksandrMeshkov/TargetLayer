from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.team import Team
from app.models.team_member import TeamMember
from app.models.user import User
from app.models.team_role import TeamRole


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
	stmt_role = select(TeamRole).where(TeamRole.name == "Администратор")
	res_role = await db.execute(stmt_role)
	admin_role = res_role.scalar_one_or_none()
	if not admin_role:
		admin_role = TeamRole(name="Администратор")
		db.add(admin_role)
		await db.flush()
	owner_membership = TeamMember(
		team_id=team.team_id,
		user_id=user.user_id,
		team_role_id=admin_role.team_role_id,
	)
	db.add(owner_membership)
	await db.commit()
	await db.refresh(team)
	return team
