
from fastapi import HTTPException, status
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.team_member import TeamMember
from app.models.user import User

async def leave_team(db: AsyncSession, user: User, team_id: int) -> None:
	stmt = select(TeamMember).where(
		TeamMember.team_id == team_id,
		TeamMember.user_id == user.user_id,
	)
	result = await db.execute(stmt)
	membership = result.scalar_one_or_none()
	if not membership:
		raise HTTPException(
			status_code=status.HTTP_404_NOT_FOUND,
			detail="User is not a member of this team",
		)
	await db.delete(membership)
	await db.commit()
