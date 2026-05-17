from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chat import Chat
from app.services.chat.chat_permissions import ensure_user_is_chat_participant


async def rename_chat(
	db: AsyncSession,
	*,
	chat_id: int,
	user_id: int,
	new_name: str,
) -> Chat:
	
	await ensure_user_is_chat_participant(db, chat_id=chat_id, user_id=user_id)
	
	stmt = select(Chat).where(Chat.chat_id == chat_id)
	result = await db.execute(stmt)
	chat = result.scalar_one_or_none()
	
	if not chat:
		raise HTTPException(
			status_code=status.HTTP_404_NOT_FOUND,
			detail="Чат не найден"
		)
	
	chat.name = new_name
	await db.commit()
	await db.refresh(chat)
	
	return chat
