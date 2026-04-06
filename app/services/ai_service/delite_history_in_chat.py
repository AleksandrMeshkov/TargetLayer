from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai_conversation import AIConversation


async def delete_ai_conversation(
	db: AsyncSession,
	current_user_id: int,
	conversation_id: int,
) -> dict:
	stmt = select(AIConversation).where(AIConversation.conversation_id == conversation_id)
	result = await db.execute(stmt)
	conversation = result.scalar_one_or_none()
	if not conversation or conversation.user_id != current_user_id:
		raise HTTPException(
			status_code=status.HTTP_404_NOT_FOUND,
			detail="Conversation not found",
		)

	await db.delete(conversation)
	await db.commit()

	return {"status": "deleted", "conversation_id": conversation_id}
