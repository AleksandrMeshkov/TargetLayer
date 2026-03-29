from typing import List, Dict, Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.ai_conversation import AIConversation
from app.models.ai_message import AIMessage
from app.models.ai_message_role import AIMessageRole


async def _get_or_create_ai_message_role(db: AsyncSession, role_name: str) -> AIMessageRole:
	stmt = select(AIMessageRole).where(AIMessageRole.name == role_name)
	result = await db.execute(stmt)
	role = result.scalar_one_or_none()
	if role:
		return role

	role = AIMessageRole(name=role_name)
	db.add(role)
	await db.flush()
	return role


async def create_conversation(db: AsyncSession, user_id: int) -> int:
	conversation = AIConversation(user_id=user_id)
	db.add(conversation)
	await db.flush()
	await db.commit()
	return conversation.conversation_id


async def save_chat(
	db: AsyncSession,
	user_id: int,
	user_content: str,
	ai_content: str,
	conversation_id: Optional[int] = None,
) -> int:
	
	if conversation_id is not None:
		stmt = select(AIConversation).where(AIConversation.conversation_id == conversation_id)
		res = await db.execute(stmt)
		conv = res.scalar_one_or_none()
		if not conv or conv.user_id != user_id:
			raise ValueError("Conversation not found or does not belong to user")
	else:
		conv = AIConversation(user_id=user_id)
		db.add(conv)
		await db.flush()
		conversation_id = conv.conversation_id

	user_role = await _get_or_create_ai_message_role(db, "user")
	assistant_role = await _get_or_create_ai_message_role(db, "assistant")

	user_msg = AIMessage(
		conversation_id=conversation_id,
		ai_message_role_id=user_role.ai_message_role_id,
		content=user_content,
	)
	ai_msg = AIMessage(
		conversation_id=conversation_id,
		ai_message_role_id=assistant_role.ai_message_role_id,
		content=ai_content,
	)
	db.add_all([user_msg, ai_msg])
	await db.commit()
	return conversation_id


async def fetch_history(db: AsyncSession, user_id: int) -> List[Dict[str, Any]]:
	stmt = select(AIConversation).where(AIConversation.user_id == user_id).order_by(AIConversation.created_at.desc())
	result = await db.execute(stmt)
	conversations = result.scalars().all()

	history = []
	for conv in conversations:
		msg_stmt = (
			select(AIMessage)
			.options(selectinload(AIMessage.ai_message_role))
			.where(AIMessage.conversation_id == conv.conversation_id)
			.order_by(AIMessage.created_at)
		)
		msg_res = await db.execute(msg_stmt)
		messages = msg_res.scalars().all()

		history.append({
			"conversation_id": conv.conversation_id,
			"created_at": conv.created_at,
			"updated_at": conv.updated_at,
			"messages": [
				{
					"message_id": m.message_id,
					"role": m.ai_message_role.name if m.ai_message_role else None,
					"content": m.content,
					"created_at": m.created_at,
				}
				for m in messages
			],
		})

	return history
