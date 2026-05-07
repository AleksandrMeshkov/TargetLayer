from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.team_role import TeamRole


async def init_team_roles(db: AsyncSession) -> None:
	roles_to_create = [
		(1, "Администратор"),
		(2, "Участник"),
	]
	
	for role_id, role_name in roles_to_create:
		stmt = select(TeamRole).where(TeamRole.team_role_id == role_id)
		result = await db.execute(stmt)
		existing_role = result.scalar_one_or_none()
		
		if existing_role is None:
			role = TeamRole(team_role_id=role_id, name=role_name)
			db.add(role)
	
	await db.commit()
