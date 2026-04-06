from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security.jwt import InviteJWTManager
from app.models.team_access_link import TeamAccessLink
from app.models.team_member import TeamMember
from app.models.user import User
from app.services.team_service.get_or_create_team_role import get_or_create_team_role
from app.services.team_service.invite_token import hash_invite_token


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

    jwt_manager = InviteJWTManager()
    try:
        team_id_from_token = jwt_manager.verify_team_invite_token(raw_token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid invite token",
        )

    token_hash = hash_invite_token(raw_token)
    stmt = select(TeamAccessLink).where(TeamAccessLink.token_hash == token_hash)
    result = await db.execute(stmt)
    access_link = result.scalar_one_or_none()
    if not access_link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invite link not found",
        )

    if access_link.team_id != team_id_from_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid invite token",
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
