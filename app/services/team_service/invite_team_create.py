from datetime import datetime, timedelta, timezone
import hashlib
import secrets

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security.jwt import JWTManager
from app.core.settings.settings import settings
from app.models.team_access_link import TeamAccessLink
from app.models.team_member import TeamMember
from app.models.user import User
from app.services.team_service.get_or_create_team_role import get_or_create_team_role
from app.services.team_service.get_owned_team import get_owned_team


def _hash_token(token: str) -> str:
	return hashlib.sha256(token.encode("utf-8")).hexdigest()


async def create_team_invite_link(
	db: AsyncSession,
	current_user: User,
	team_id: int,
	uses_left: int = 1,
) -> dict:
	await get_owned_team(db, current_user, team_id)

	# По текущему правилу: создатель команды = "Администратор",
	# все присоединившиеся пользователи = "Участник".
	# Поэтому любые инвайты создаём только с permission="Участник".
	permission = "Участник"

	# Роли в проекте: только "Администратор" и "Участник".
	# Поддерживаем legacy значения owner/member.
	role = await get_or_create_team_role(db, permission)
	normalized_permission = role.name

	normalized_uses = max(1, uses_left)
	jwt_manager = JWTManager()

	nonce = secrets.token_urlsafe(24)
	subject = f"team:{team_id}:{nonce}"
	token = jwt_manager.create_invite_token(subject)

	now = datetime.now(timezone.utc)
	expires_at = now + timedelta(hours=getattr(settings, "INVITE_TOKEN_EXPIRE_HOURS", 24))
	access_link = TeamAccessLink(
		team_id=team_id,
		token_hash=_hash_token(token),
		permission=normalized_permission,
		expires_at=expires_at,
		used_at=None,
		uses_left=normalized_uses,
		created_by_user_id=current_user.user_id,
	)
	db.add(access_link)
	await db.commit()
	await db.refresh(access_link)

	return {
		"token": token,
		"team_id": team_id,
		"permission": access_link.permission,
		"uses_left": access_link.uses_left,
		"expires_at": access_link.expires_at,
	}


async def accept_team_invite(
	db: AsyncSession,
	current_user: User,
	token: str,
) -> dict:
	raw_token = (token or "").strip()
	if not raw_token:
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail="Invite token is required",
		)

	jwt_manager = JWTManager()
	try:
		jwt_manager.verify_invite_token(raw_token)
	except Exception:
		raise HTTPException(
			status_code=status.HTTP_401_UNAUTHORIZED,
			detail="Invalid invite token",
		)

	token_hash = _hash_token(raw_token)
	stmt = select(TeamAccessLink).where(TeamAccessLink.token_hash == token_hash)
	result = await db.execute(stmt)
	access_link = result.scalar_one_or_none()
	if not access_link:
		raise HTTPException(
			status_code=status.HTTP_404_NOT_FOUND,
			detail="Invite link not found",
		)

	now = datetime.now(timezone.utc)
	if access_link.expires_at < now:
		raise HTTPException(
			status_code=status.HTTP_410_GONE,
			detail="Invite link has expired",
		)
	if access_link.used_at is not None:
		raise HTTPException(
			status_code=status.HTTP_410_GONE,
			detail="Invite link already used",
		)
	if access_link.uses_left is not None and access_link.uses_left <= 0:
		raise HTTPException(
			status_code=status.HTTP_410_GONE,
			detail="Invite link has no remaining uses",
		)

	existing_member_stmt = select(TeamMember).where(
		TeamMember.team_id == access_link.team_id,
		TeamMember.user_id == current_user.user_id,
	)
	existing_member_result = await db.execute(existing_member_stmt)
	existing_member = existing_member_result.scalar_one_or_none()
	if existing_member:
		return {
			"team_id": existing_member.team_id,
			"user_id": existing_member.user_id,
			"team_role_id": existing_member.team_role_id,
			"joined_at": existing_member.joined_at,
			"status": "already_member",
		}

	# По текущему правилу: все, кто присоединился к команде (не создатель) — "Участник".
	role = await get_or_create_team_role(db, "Участник")
	if access_link.permission != role.name:
		access_link.permission = role.name
	membership = TeamMember(
		team_id=access_link.team_id,
		user_id=current_user.user_id,
		team_role_id=role.team_role_id,
	)
	db.add(membership)

	if access_link.uses_left is not None:
		access_link.uses_left -= 1
		if access_link.uses_left <= 0:
			access_link.used_at = now

	db.add(access_link)
	await db.commit()
	await db.refresh(membership)

	return {
		"team_id": membership.team_id,
		"user_id": membership.user_id,
		"team_role_id": membership.team_role_id,
		"joined_at": membership.joined_at,
		"status": "joined",
	}
