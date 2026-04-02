from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.message import Message
from app.services.chat.chat_permissions import ensure_user_is_chat_participant


async def list_chat_messages(db: AsyncSession, *, chat_id: int, user_id: int) -> list[Message]:
	await ensure_user_is_chat_participant(db, chat_id=chat_id, user_id=user_id)
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
	await ensure_user_is_chat_participant(db, chat_id=chat_id, user_id=user_id)
	text = (content or "").strip()
	if not text:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Сообщение пустое")

	msg = Message(chat_id=chat_id, user_id=user_id, type=message_type, content=text)
	db.add(msg)
	await db.commit()
	await db.refresh(msg)
	return msg


async def delete_chat_message(db: AsyncSession, *, chat_id: int, message_id: int, user_id: int) -> None:
	await ensure_user_is_chat_participant(db, chat_id=chat_id, user_id=user_id)
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
