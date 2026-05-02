from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chat import Chat
from app.models.chat_participant import ChatParticipant
from app.models.team_member import TeamMember


async def ensure_user_in_team(db: AsyncSession, *, user_id: int, team_id: int) -> None:
	stmt = select(TeamMember.id).where(
		TeamMember.team_id == team_id,
		TeamMember.user_id == user_id,
	)
	res = await db.execute(stmt)
	if res.scalar_one_or_none() is None:
		raise HTTPException(
			status_code=status.HTTP_403_FORBIDDEN,
			detail="Пользователь не состоит в команде",
		)


async def ensure_user_is_chat_participant(db: AsyncSession, *, chat_id: int, user_id: int) -> None:
	chat_stmt = select(Chat).where(Chat.chat_id == chat_id)
	chat_res = await db.execute(chat_stmt)
	chat = chat_res.scalar_one_or_none()
	
	if not chat:
		raise HTTPException(
			status_code=status.HTTP_403_FORBIDDEN,
			detail="Чат не найден",
		)
	
	if chat.team_id:
		member_stmt = select(TeamMember.id).where(
			TeamMember.team_id == chat.team_id,
			TeamMember.user_id == user_id,
		)
		member_res = await db.execute(member_stmt)
		if member_res.scalar_one_or_none() is None:
			raise HTTPException(
				status_code=status.HTTP_403_FORBIDDEN,
				detail="Пользователь не состоит в команде этого чата",
			)
	
	participant_stmt = select(ChatParticipant.id).where(
		ChatParticipant.chat_id == chat_id,
		ChatParticipant.user_id == user_id,
	)
	participant_res = await db.execute(participant_stmt)
	if participant_res.scalar_one_or_none() is None:
		raise HTTPException(
			status_code=status.HTTP_403_FORBIDDEN,
			detail="Нет доступа к чату",
		)
