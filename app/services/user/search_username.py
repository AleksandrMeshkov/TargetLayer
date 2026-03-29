from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


async def search_users_by_username(
	db: AsyncSession,
	username_query: str,
	limit: int = 50,
) -> list[User]:
	query = (username_query or "").strip()
	if not query:
		return []

	stmt = (
		select(User)
		.where(func.lower(User.username).contains(query.lower()))
		.order_by(User.username.asc(), User.user_id.asc())
		.limit(limit)
	)
	result = await db.execute(stmt)
	return list(result.scalars().all())
