
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Path, Security, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database.database import get_db
from app.models.chat import Chat
from app.models.message import Message
from app.models.user import User
from app.services.chat.team_chat import get_or_create_team_chat
from app.services.chat.user_chat import (
	create_group_chat,
	list_chat_participants,
	list_my_chats,
	delete_chat_message,
	leave_chat,
	list_chat_messages,
	send_chat_message,
)
from app.services.user.get_my_user import get_current_user


router = APIRouter(prefix="/api/v1/chats", tags=["chats"])


class ChatCreateRequest(BaseModel):
	team_id: int = Field(gt=0)
	participant_user_ids: list[int] = Field(default_factory=list)
	name: str | None = Field(default=None, max_length=255)


class ChatResponse(BaseModel):
	chat_id: int
	team_id: int
	type: str
	name: str | None
	created_at: datetime

	model_config = ConfigDict(from_attributes=True)


class MessageCreateRequest(BaseModel):
	content: str = Field(min_length=1)
	type: str = Field(default="text", max_length=50)


class MessageResponse(BaseModel):
	message_id: int
	chat_id: int
	user_id: int
	type: str
	content: str
	created_at: datetime

	model_config = ConfigDict(from_attributes=True)


class MessagesListResponse(BaseModel):
	messages: list[MessageResponse]
	total: int


class ChatListResponse(BaseModel):
	chats: list[ChatResponse]
	total: int


class ChatParticipantResponse(BaseModel):
	id: int
	chat_id: int
	user_id: int
	joined_at: datetime

	model_config = ConfigDict(from_attributes=True)


class ChatParticipantsListResponse(BaseModel):
	participants: list[ChatParticipantResponse]
	total: int


@router.post(
	"",
	response_model=ChatResponse,
	status_code=status.HTTP_201_CREATED,
	openapi_extra={"security": [{"Bearer": []}]},
)
async def create_chat(
	payload: ChatCreateRequest,
	current_user: User = Security(get_current_user),
	db: AsyncSession = Depends(get_db),
) -> Chat:
	chat = await create_group_chat(
		db,
		team_id=payload.team_id,
		creator_user_id=current_user.user_id,
		participant_user_ids=payload.participant_user_ids,
		name=payload.name,
	)
	return chat


@router.get(
	"/my",
	response_model=ChatListResponse,
	openapi_extra={"security": [{"Bearer": []}]},
)
async def get_my_chats(
	current_user: User = Security(get_current_user),
	db: AsyncSession = Depends(get_db),
) -> ChatListResponse:
	chats = await list_my_chats(db, user_id=current_user.user_id)
	return ChatListResponse(chats=chats, total=len(chats))


@router.post(
	"/team/{team_id}",
	response_model=ChatResponse,
	openapi_extra={"security": [{"Bearer": []}]},
)
async def get_or_create_team_chat_endpoint(
	team_id: int = Path(..., gt=0),
	current_user: User = Security(get_current_user),
	db: AsyncSession = Depends(get_db),
) -> Chat:
	chat = await get_or_create_team_chat(db, team_id=team_id, user_id=current_user.user_id)
	return chat


@router.get(
	"/{chat_id}/messages",
	response_model=MessagesListResponse,
	openapi_extra={"security": [{"Bearer": []}]},
)
async def get_chat_messages(
	chat_id: int = Path(..., gt=0),
	current_user: User = Security(get_current_user),
	db: AsyncSession = Depends(get_db),
) -> MessagesListResponse:
	messages = await list_chat_messages(db, chat_id=chat_id, user_id=current_user.user_id)
	return MessagesListResponse(messages=messages, total=len(messages))


@router.get(
	"/{chat_id}/participants",
	response_model=ChatParticipantsListResponse,
	openapi_extra={"security": [{"Bearer": []}]},
)
async def get_chat_participants(
	chat_id: int = Path(..., gt=0),
	current_user: User = Security(get_current_user),
	db: AsyncSession = Depends(get_db),
) -> ChatParticipantsListResponse:
	participants = await list_chat_participants(db, chat_id=chat_id, user_id=current_user.user_id)
	return ChatParticipantsListResponse(participants=participants, total=len(participants))


@router.post(
	"/{chat_id}/messages",
	response_model=MessageResponse,
	status_code=status.HTTP_201_CREATED,
	openapi_extra={"security": [{"Bearer": []}]},
)
async def post_chat_message(
	payload: MessageCreateRequest,
	chat_id: int = Path(..., gt=0),
	current_user: User = Security(get_current_user),
	db: AsyncSession = Depends(get_db),
) -> Message:
	msg = await send_chat_message(
		db,
		chat_id=chat_id,
		user_id=current_user.user_id,
		content=payload.content,
		message_type=payload.type,
	)
	return msg


@router.delete(
	"/{chat_id}/messages/{message_id}",
	response_model=dict,
	openapi_extra={"security": [{"Bearer": []}]},
)
async def delete_message(
	chat_id: int = Path(..., gt=0),
	message_id: int = Path(..., gt=0),
	current_user: User = Security(get_current_user),
	db: AsyncSession = Depends(get_db),
) -> dict:
	await delete_chat_message(db, chat_id=chat_id, message_id=message_id, user_id=current_user.user_id)
	return {"status": "success", "message": "Сообщение удалено"}


@router.delete(
	"/{chat_id}/leave",
	response_model=dict,
	openapi_extra={"security": [{"Bearer": []}]},
)
async def leave_chat_endpoint(
	chat_id: int = Path(..., gt=0),
	current_user: User = Security(get_current_user),
	db: AsyncSession = Depends(get_db),
) -> dict:
	await leave_chat(db, chat_id=chat_id, user_id=current_user.user_id)
	return {"status": "success", "message": "Вы вышли из чата"}
