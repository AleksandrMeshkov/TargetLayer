
from __future__ import annotations

from fastapi import APIRouter, Depends, Path, Security, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database.database import get_db
from app.models.chat import Chat
from app.models.message import Message
from app.models.user import User
from app.schemas import chat as chat_schemas
from app.services.chat.team_chat import get_or_create_team_chat as get_or_create_team_chat_service
from app.services.chat.group_chat_service import create_group_chat
from app.services.chat.message_service import delete_chat_message, list_chat_messages, send_chat_message
from app.services.chat.participant_service import (
	leave_chat as leave_chat_service,
	list_chat_participants,
	list_my_chats,
)
from app.services.user.get_my_user import get_current_user


router = APIRouter(prefix="/api/v1/chats", tags=["chats"])


@router.post(
	"",
	response_model=chat_schemas.ChatResponse,
	status_code=status.HTTP_201_CREATED,
	openapi_extra={"security": [{"Bearer": []}]},
)
async def create_chat(
	payload: chat_schemas.ChatCreateRequest,
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
	response_model=chat_schemas.ChatListResponse,
	openapi_extra={"security": [{"Bearer": []}]},
)
async def get_my_chats(
	current_user: User = Security(get_current_user),
	db: AsyncSession = Depends(get_db),
) -> chat_schemas.ChatListResponse:
	chats = await list_my_chats(db, user_id=current_user.user_id)
	return chat_schemas.ChatListResponse(chats=chats, total=len(chats))


@router.post(
	"/team/{team_id}",
	response_model=chat_schemas.ChatResponse,
	openapi_extra={"security": [{"Bearer": []}]},
)
async def get_or_create_team_chat_endpoint(
	team_id: int = Path(..., gt=0),
	current_user: User = Security(get_current_user),
	db: AsyncSession = Depends(get_db),
) -> Chat:
	chat = await get_or_create_team_chat_service(db, team_id=team_id, user_id=current_user.user_id)
	return chat


@router.get(
	"/{chat_id}/messages",
	response_model=chat_schemas.MessagesListResponse,
	openapi_extra={"security": [{"Bearer": []}]},
)
async def get_chat_messages(
	chat_id: int = Path(..., gt=0),
	current_user: User = Security(get_current_user),
	db: AsyncSession = Depends(get_db),
) -> chat_schemas.MessagesListResponse:
	messages = await list_chat_messages(db, chat_id=chat_id, user_id=current_user.user_id)
	return chat_schemas.MessagesListResponse(messages=messages, total=len(messages))


@router.get(
	"/{chat_id}/participants",
	response_model=chat_schemas.ChatParticipantsListResponse,
	openapi_extra={"security": [{"Bearer": []}]},
)
async def get_chat_participants(
	chat_id: int = Path(..., gt=0),
	current_user: User = Security(get_current_user),
	db: AsyncSession = Depends(get_db),
) -> chat_schemas.ChatParticipantsListResponse:
	participants = await list_chat_participants(db, chat_id=chat_id, user_id=current_user.user_id)
	return chat_schemas.ChatParticipantsListResponse(participants=participants, total=len(participants))


@router.post(
	"/{chat_id}/messages",
	response_model=chat_schemas.MessageResponse,
	status_code=status.HTTP_201_CREATED,
	openapi_extra={"security": [{"Bearer": []}]},
)
async def post_chat_message(
	payload: chat_schemas.MessageCreateRequest,
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
	await leave_chat_service(db, chat_id=chat_id, user_id=current_user.user_id)
	return {"status": "success", "message": "Вы вышли из чата"}
