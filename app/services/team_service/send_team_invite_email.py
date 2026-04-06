from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.email.message_sender import MessageSender
from app.core.security.jwt import InviteJWTManager
from app.core.settings.settings import settings
from app.models.team_access_link import TeamAccessLink
from app.models.user import User
from app.services.team_service.get_or_create_team_role import get_or_create_team_role
from app.services.team_service.get_owned_team import get_owned_team
from app.services.team_service.invite_token import hash_invite_token


async def send_team_invite_email(
    db: AsyncSession,
    current_user: User,
    team_id: int,
    invited_user_id: int,
) -> dict:
    await get_owned_team(db, current_user, team_id)

    stmt = select(User).where(User.user_id == invited_user_id)
    result = await db.execute(stmt)
    invited_user = result.scalar_one_or_none()

    if not invited_user or not invited_user.email:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    role = await get_or_create_team_role(db, "Участник")
    jwt_manager = InviteJWTManager()
    token = jwt_manager.create_team_invite_token(team_id)

    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(hours=getattr(settings, "INVITE_TOKEN_EXPIRE_HOURS", 24))
    access_link = TeamAccessLink(
        team_id=team_id,
        token_hash=hash_invite_token(token),
        permission=role.name,
        expires_at=expires_at,
        used_at=None,
        uses_left=1,
        created_by_user_id=current_user.user_id,
    )
    db.add(access_link)
    await db.commit()
    await db.refresh(access_link)

    sender = MessageSender()
    email_sent = await sender.send_team_invite_link(invited_user.email, token)
    if not email_sent:
        raise HTTPException(status_code=400, detail="Ошибка при отправке письма приглашения")

    return {
        "status": "sent",
        "email": invited_user.email,
        "team_id": team_id,
        "expires_at": access_link.expires_at,
    }
