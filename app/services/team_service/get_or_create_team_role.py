from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.team_role import TeamRole


async def get_or_create_team_role(db: AsyncSession, role_name: str) -> TeamRole:
	stmt = select(TeamRole).where(TeamRole.name == role_name)
	res = await db.execute(stmt)
	role = res.scalar_one_or_none()
	if role:
		return role

	role = TeamRole(name=role_name)
	db.add(role)
	await db.flush()
	return role
