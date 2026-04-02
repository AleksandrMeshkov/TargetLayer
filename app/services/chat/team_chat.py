
from __future__ import annotations

from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chat import Chat
from app.models.chat_participant import ChatParticipant
from app.models.team_member import TeamMember


async def get_or_create_team_chat(db: AsyncSession, *, team_id: int, user_id: int) -> Chat:
	member_stmt = select(TeamMember.id).where(
		TeamMember.team_id == team_id,
		TeamMember.user_id == user_id,
	)
	member_res = await db.execute(member_stmt)
	if member_res.scalar_one_or_none() is None:
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Пользователь не состоит в команде")

	existing_stmt = select(Chat).where(Chat.team_id == team_id, Chat.type == "team")
	existing_res = await db.execute(existing_stmt)
	existing = existing_res.scalar_one_or_none()
	if existing:
		participant_stmt = select(ChatParticipant.id).where(
			ChatParticipant.chat_id == existing.chat_id,
			ChatParticipant.user_id == user_id,
		)
		participant_res = await db.execute(participant_stmt)
		if participant_res.scalar_one_or_none() is None:
			db.add(ChatParticipant(chat_id=existing.chat_id, user_id=user_id, joined_at=datetime.utcnow()))
			await db.commit()
			await db.refresh(existing)
		return existing

	chat = Chat(team_id=team_id, type="team", name="Общий чат")
	db.add(chat)
	await db.flush()

	members_stmt = select(TeamMember.user_id).where(TeamMember.team_id == team_id)
	members_res = await db.execute(members_stmt)
	member_user_ids = list(members_res.scalars().all())
	for uid in member_user_ids:
		db.add(ChatParticipant(chat_id=chat.chat_id, user_id=uid, joined_at=datetime.utcnow()))

	await db.commit()
	await db.refresh(chat)
	return chat
