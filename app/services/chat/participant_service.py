from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chat import Chat
from app.models.chat_participant import ChatParticipant
from app.services.chat.chat_permissions import ensure_user_is_chat_participant


async def leave_chat(db: AsyncSession, *, chat_id: int, user_id: int) -> None:
	stmt = select(ChatParticipant).where(
		ChatParticipant.chat_id == chat_id,
		ChatParticipant.user_id == user_id,
	)
	res = await db.execute(stmt)
	participant = res.scalar_one_or_none()
	if not participant:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Вы не состоите в этом чате")

	await db.delete(participant)
	await db.commit()


async def list_my_chats(db: AsyncSession, *, user_id: int) -> list[Chat]:
	stmt = (
		select(Chat)
		.join(ChatParticipant, ChatParticipant.chat_id == Chat.chat_id)
		.where(ChatParticipant.user_id == user_id)
		.order_by(Chat.created_at.desc())
	)
	res = await db.execute(stmt)
	return list(res.scalars().unique().all())


async def list_chat_participants(db: AsyncSession, *, chat_id: int, user_id: int) -> list[ChatParticipant]:
	await ensure_user_is_chat_participant(db, chat_id=chat_id, user_id=user_id)
	stmt = select(ChatParticipant).where(ChatParticipant.chat_id == chat_id).order_by(ChatParticipant.joined_at.asc())
	res = await db.execute(stmt)
	return list(res.scalars().all())
