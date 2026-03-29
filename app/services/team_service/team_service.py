from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.models.team import Team
from app.models.team_member import TeamMember
from app.models.team_role import TeamRole
from app.models.user import User


class TeamService:
	def __init__(self, db: AsyncSession):
		self.db = db

	async def get_team_members(self, user: User, team_id: int) -> list[dict]:
		team_stmt = select(Team).where(Team.team_id == team_id)
		team_result = await self.db.execute(team_stmt)
		team = team_result.scalar_one_or_none()
		if not team:
			raise HTTPException(
				status_code=status.HTTP_404_NOT_FOUND,
				detail="Team not found",
			)

		access_stmt = select(TeamMember).where(
			TeamMember.team_id == team_id,
			TeamMember.user_id == user.user_id,
		)
		access_result = await self.db.execute(access_stmt)
		membership = access_result.scalar_one_or_none()
		if not membership:
			raise HTTPException(
				status_code=status.HTTP_403_FORBIDDEN,
				detail="You do not have access to this team",
			)

		members_stmt = (
			select(
				TeamMember.id,
				TeamMember.team_id,
				TeamMember.user_id,
				TeamMember.team_role_id,
				TeamMember.joined_at,
			)
			.where(TeamMember.team_id == team_id)
			.order_by(TeamMember.joined_at.asc(), TeamMember.id.asc())
		)
		members_result = await self.db.execute(members_stmt)
		return [dict(row) for row in members_result.mappings().all()]

	async def _get_owned_team(self, user: User, team_id: int) -> Team:
		team_stmt = select(Team).where(Team.team_id == team_id)
		team_result = await self.db.execute(team_stmt)
		team = team_result.scalar_one_or_none()
		if not team:
			raise HTTPException(
				status_code=status.HTTP_404_NOT_FOUND,
				detail="Team not found",
			)

		owner_stmt = (
			select(TeamMember)
			.join(TeamRole, TeamRole.team_role_id == TeamMember.team_role_id)
			.where(
				TeamMember.team_id == team_id,
				TeamMember.user_id == user.user_id,
				TeamRole.name == "owner",
			)
		)
		owner_result = await self.db.execute(owner_stmt)
		owner = owner_result.scalar_one_or_none()
		if not owner:
			raise HTTPException(
				status_code=status.HTTP_403_FORBIDDEN,
				detail="Only team owner can manage this team",
			)

		return team

	async def get_user_teams(self, user: User) -> list[Team]:
		stmt = (
			select(Team)
			.join(TeamMember, TeamMember.team_id == Team.team_id)
			.where(TeamMember.user_id == user.user_id)
			.order_by(Team.created_at.desc())
		)
		result = await self.db.execute(stmt)
		return list(result.scalars().unique().all())

	async def _get_or_create_team_role(self, role_name: str) -> TeamRole:
		stmt = select(TeamRole).where(TeamRole.name == role_name)
		res = await self.db.execute(stmt)
		role = res.scalar_one_or_none()
		if role:
			return role

		role = TeamRole(name=role_name)
		self.db.add(role)
		await self.db.flush()
		return role

	async def create_team(self, user: User, name: str) -> Team:
		team_name = (name or "").strip()
		if not team_name:
			raise HTTPException(
				status_code=status.HTTP_400_BAD_REQUEST,
				detail="Team name is required",
			)

		existing_stmt = select(Team).where(Team.name == team_name)
		existing_result = await self.db.execute(existing_stmt)
		if existing_result.scalar_one_or_none():
			raise HTTPException(
				status_code=status.HTTP_409_CONFLICT,
				detail="Team with this name already exists",
			)

		team = Team(name=team_name)
		self.db.add(team)
		await self.db.flush()

		owner_role = await self._get_or_create_team_role("owner")
		owner_membership = TeamMember(
			team_id=team.team_id,
			user_id=user.user_id,
			team_role_id=owner_role.team_role_id,
		)
		self.db.add(owner_membership)
		await self.db.commit()
		await self.db.refresh(team)
		return team

	async def delete_team(self, user: User, team_id: int) -> None:
		team = await self._get_owned_team(user, team_id)
		await self.db.delete(team)
		await self.db.commit()

	async def rename_team(self, user: User, team_id: int, name: str) -> Team:
		team = await self._get_owned_team(user, team_id)

		new_name = (name or "").strip()
		if not new_name:
			raise HTTPException(
				status_code=status.HTTP_400_BAD_REQUEST,
				detail="Team name is required",
			)

		existing_stmt = select(Team).where(Team.name == new_name, Team.team_id != team_id)
		existing_result = await self.db.execute(existing_stmt)
		if existing_result.scalar_one_or_none():
			raise HTTPException(
				status_code=status.HTTP_409_CONFLICT,
				detail="Team with this name already exists",
			)

		team.name = new_name
		self.db.add(team)
		await self.db.commit()
		await self.db.refresh(team)
		return team
