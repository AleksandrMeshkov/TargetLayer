from typing import List, Dict, Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.ai_conversation import AIConversation
from app.models.ai_message import AIMessage


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

	user_msg = AIMessage(conversation_id=conversation_id, role="user", content=user_content)
	ai_msg = AIMessage(conversation_id=conversation_id, role="assistant", content=ai_content)
	db.add_all([user_msg, ai_msg])
	await db.commit()
	return conversation_id


async def fetch_history(db: AsyncSession, user_id: int) -> List[Dict[str, Any]]:
	stmt = select(AIConversation).where(AIConversation.user_id == user_id).order_by(AIConversation.created_at.desc())
	result = await db.execute(stmt)
	conversations = result.scalars().all()

	history = []
	for conv in conversations:
		msg_stmt = select(AIMessage).where(AIMessage.conversation_id == conv.conversation_id).order_by(AIMessage.created_at)
		msg_res = await db.execute(msg_stmt)
		messages = msg_res.scalars().all()

		history.append({
			"conversation_id": conv.conversation_id,
			"created_at": conv.created_at,
			"updated_at": conv.updated_at,
			"messages": [
				{"message_id": m.message_id, "role": m.role, "content": m.content, "created_at": m.created_at}
				for m in messages
			],
		})

	return history
