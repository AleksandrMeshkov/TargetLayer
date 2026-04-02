from __future__ import annotations

from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chat import Chat
from app.models.chat_participant import ChatParticipant
from app.models.team_member import TeamMember
from app.services.chat.chat_permissions import ensure_user_in_team


async def create_group_chat(
	db: AsyncSession,
	*,
	team_id: int,
	creator_user_id: int,
	participant_user_ids: list[int],
	name: str | None = None,
) -> Chat:
	await ensure_user_in_team(db, user_id=creator_user_id, team_id=team_id)

	normalized_ids = [int(uid) for uid in participant_user_ids if uid is not None]
	participant_set = {creator_user_id, *normalized_ids}

	if len(participant_set) < 2:
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail="Нужно выбрать минимум одного участника кроме себя",
		)

	members_stmt = select(TeamMember.user_id).where(TeamMember.team_id == team_id)
	members_res = await db.execute(members_stmt)
	team_user_ids = set(members_res.scalars().all())

	if not participant_set.issubset(team_user_ids):
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail="Все участники должны быть из одной команды",
		)

	chat = Chat(team_id=team_id, type="group", name=(name or None))
	db.add(chat)
	await db.flush()

	for uid in sorted(participant_set):
		db.add(ChatParticipant(chat_id=chat.chat_id, user_id=uid, joined_at=datetime.utcnow()))

	await db.commit()
	await db.refresh(chat)
	return chat
