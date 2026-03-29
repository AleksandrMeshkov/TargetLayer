from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.services.team_service.get_owned_team import get_owned_team


async def delete_team(db: AsyncSession, user: User, team_id: int) -> None:
	team = await get_owned_team(db, user, team_id)
	await db.delete(team)
	await db.commit()
