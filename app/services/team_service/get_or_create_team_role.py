from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.team_role import TeamRole


def _normalize_team_role_name(role_name: str) -> str:
	raw = (role_name or "").strip()
	if not raw:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Роль не указана")

	lower = raw.lower()
	if lower in {"администратор", "administrator", "admin", "owner"}:
		return "Администратор"
	if lower in {"участник", "participant", "member"}:
		return "Участник"

	raise HTTPException(
		status_code=status.HTTP_400_BAD_REQUEST,
		detail="Разрешены только роли: Администратор, Участник",
	)


async def get_or_create_team_role(db: AsyncSession, role_name: str) -> TeamRole:
	role_name = _normalize_team_role_name(role_name)
	stmt = select(TeamRole).where(TeamRole.name == role_name)
	res = await db.execute(stmt)
	role = res.scalar_one_or_none()
	if role:
		return role

	role = TeamRole(name=role_name)
	db.add(role)
	await db.flush()
	return role
