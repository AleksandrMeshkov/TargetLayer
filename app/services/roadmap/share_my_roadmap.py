from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status
from app.models.roadmap import Roadmap
from app.models.team import Team
from app.models.team_member import TeamMember
from app.models.team_role import TeamRole

async def share_roadmap_with_team(db: AsyncSession, user_id: int, roadmap_id: int, team_id: int):
	# Получаем роудмап
	roadmap = await db.get(Roadmap, roadmap_id)
	if not roadmap:
		raise HTTPException(status_code=404, detail="Роудмап не найден")

	# Проверяем, что пользователь владеет роудмапом (goal.user_id)
	if roadmap.team_id is not None:
		raise HTTPException(status_code=400, detail="Роудмап уже принадлежит команде")

	# Проверяем, что пользователь состоит в команде и является Администратором
	stmt = select(TeamMember).join(TeamRole).where(
		TeamMember.team_id == team_id,
		TeamMember.user_id == user_id,
		TeamRole.name == "Администратор"
	)
	result = await db.execute(stmt)
	admin_member = result.scalar_one_or_none()
	if not admin_member:
		raise HTTPException(status_code=403, detail="Только Администратор может делиться роудмапом с командой")

	# Передаем роудмап команде
	roadmap.team_id = team_id
	await db.commit()
	return {"status": "success", "message": "Роудмап передан команде"}
