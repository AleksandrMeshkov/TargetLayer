
from __future__ import annotations

from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy import and_, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chat import Chat
from app.models.chat_participant import ChatParticipant
from app.models.message import Message
from app.models.team_member import TeamMember


async def _ensure_user_in_team(db: AsyncSession, *, user_id: int, team_id: int) -> None:
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


async def _ensure_user_is_chat_participant(db: AsyncSession, *, chat_id: int, user_id: int) -> None:
	stmt = select(ChatParticipant.id).where(
		ChatParticipant.chat_id == chat_id,
		ChatParticipant.user_id == user_id,
	)
	res = await db.execute(stmt)
	if res.scalar_one_or_none() is None:
		raise HTTPException(
			status_code=status.HTTP_403_FORBIDDEN,
			detail="Нет доступа к чату",
		)


async def create_group_chat(
	db: AsyncSession,
	*,
	team_id: int,
	creator_user_id: int,
	participant_user_ids: list[int],
	name: str | None = None,
) -> Chat:
	await _ensure_user_in_team(db, user_id=creator_user_id, team_id=team_id)

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


async def list_chat_messages(db: AsyncSession, *, chat_id: int, user_id: int) -> list[Message]:
	await _ensure_user_is_chat_participant(db, chat_id=chat_id, user_id=user_id)
	stmt = select(Message).where(Message.chat_id == chat_id).order_by(Message.created_at.asc())
	res = await db.execute(stmt)
	return list(res.scalars().all())


async def send_chat_message(
	db: AsyncSession,
	*,
	chat_id: int,
	user_id: int,
	content: str,
	message_type: str = "text",
) -> Message:
	await _ensure_user_is_chat_participant(db, chat_id=chat_id, user_id=user_id)
	text = (content or "").strip()
	if not text:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Сообщение пустое")

	msg = Message(chat_id=chat_id, user_id=user_id, type=message_type, content=text)
	db.add(msg)
	await db.commit()
	await db.refresh(msg)
	return msg


async def delete_chat_message(db: AsyncSession, *, chat_id: int, message_id: int, user_id: int) -> None:
	await _ensure_user_is_chat_participant(db, chat_id=chat_id, user_id=user_id)
	stmt = select(Message).where(
		Message.message_id == message_id,
		Message.chat_id == chat_id,
	)
	res = await db.execute(stmt)
	msg = res.scalar_one_or_none()
	if not msg:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Сообщение не найдено")
	if msg.user_id != user_id:
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Можно удалить только своё сообщение")

	await db.delete(msg)
	await db.commit()


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
	await _ensure_user_is_chat_participant(db, chat_id=chat_id, user_id=user_id)
	stmt = select(ChatParticipant).where(ChatParticipant.chat_id == chat_id).order_by(ChatParticipant.joined_at.asc())
	res = await db.execute(stmt)
	return list(res.scalars().all())
