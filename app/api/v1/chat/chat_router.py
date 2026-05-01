
from __future__ import annotations

import logging
from fastapi import APIRouter, Depends, Path, Query, Security, WebSocket, WebSocketDisconnect, status
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database.database import AsyncSessionLocal, get_db
from app.core.security.jwt import JWTManager
from app.models.chat import Chat
from app.models.user import User
from app.schemas import chat as chat_schemas
from app.services.chat.chat_permissions import ensure_user_is_chat_participant
from app.services.chat.team_chat import get_or_create_team_chat as get_or_create_team_chat_service
from app.services.chat.group_chat_service import create_group_chat
from app.services.chat.message_service import delete_chat_message, list_chat_messages, send_chat_message
from app.services.chat.participant_service import (
	leave_chat as leave_chat_service,
	list_chat_participants,
	list_my_chats,
)
from app.services.user.get_my_user import get_current_user
from app.services.chat.ws_manager import chat_ws_manager


router = APIRouter(prefix="/api/v1/chats", tags=["chats"])

logger = logging.getLogger(__name__)

jwt_manager = JWTManager()


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


@router.websocket("/{chat_id}/ws")
async def chat_websocket(
	websocket: WebSocket,
	chat_id: int,
	token: str | None = Query(default=None),
	limit: int = Query(default=50, ge=1, le=200),
) -> None:
	logger.info(f"WebSocket connection attempt: chat_id={chat_id}, has_token={token is not None}")
	
	if not token:
		logger.warning(f"WebSocket rejected: No token provided for chat_id={chat_id}")
		await websocket.close(code=1008, reason="No token provided")
		return

	try:
		sub = jwt_manager.verify_access_token(token)
		user_id = int(sub)
		logger.info(f"Token verified: user_id={user_id}, chat_id={chat_id}")
	except Exception as e:
		logger.error(f"Token verification failed for chat_id={chat_id}: {str(e)}")
		await websocket.close(code=1008, reason=f"Invalid token: {str(e)}")
		return

	async with AsyncSessionLocal() as db:
		stmt = select(User).where(User.user_id == user_id)
		res = await db.execute(stmt)
		user = res.scalar_one_or_none()
		if not user:
			logger.error(f"User not found: user_id={user_id}, chat_id={chat_id}")
			await websocket.close(code=1008, reason=f"User {user_id} not found")
			return
		logger.debug(f"User found: user_id={user_id}, username={user.username if hasattr(user, 'username') else 'N/A'}")
		
		try:
			await ensure_user_is_chat_participant(db, chat_id=chat_id, user_id=user_id)
			logger.info(f"Access check passed: user_id={user_id}, chat_id={chat_id}")
		except HTTPException as e:
			logger.warning(f"Access denied: user_id={user_id}, chat_id={chat_id}, reason={e.detail}")
			await websocket.close(code=1008, reason=f"Access denied: {e.detail}")
			return

	before_online_user_ids = await chat_ws_manager.get_online_user_ids(chat_id=chat_id)
	await chat_ws_manager.connect(chat_id=chat_id, user_id=user_id, websocket=websocket)
	after_online_user_ids = await chat_ws_manager.get_online_user_ids(chat_id=chat_id)
	logger.info(f"WebSocket connected: user_id={user_id}, chat_id={chat_id}, online_users={len(after_online_user_ids)}")
	await websocket.send_json({"event": "online_users", "data": {"user_ids": after_online_user_ids}})
	if user_id not in before_online_user_ids:
		await chat_ws_manager.broadcast(
			chat_id=chat_id,
			message={"event": "presence", "data": {"user_id": user_id, "status": "online"}},
			exclude_user_id=user_id,
		)

	try:
		async with AsyncSessionLocal() as db:
			messages = await list_chat_messages(db, chat_id=chat_id, user_id=user_id)
			if limit and len(messages) > limit:
				messages = messages[-limit:]
			payload = [
				chat_schemas.MessageResponse.model_validate(m).model_dump(mode="json")
				for m in messages
			]
			logger.debug(f"Sending message history: user_id={user_id}, chat_id={chat_id}, message_count={len(payload)}")
			await websocket.send_json({"event": "history", "data": {"messages": payload, "total": len(payload)}})
	except Exception as e:
		logger.error(f"Error loading message history: user_id={user_id}, chat_id={chat_id}, error={str(e)}")
		await websocket.send_json({"event": "history", "data": {"messages": [], "total": 0}})

	try:
		while True:
			try:
				raw = await websocket.receive_json()
			except Exception:
				await websocket.send_json({"event": "error", "detail": "Invalid JSON"})
				continue

			event: str | None = None
			data = raw
			if isinstance(raw, dict):
				event = raw.get("event")
				data = raw.get("data", raw)

			# Backward-compatible: if client sends just the message payload
			if event in (None, "message"):
				try:
					msg_in = chat_schemas.MessageCreateRequest.model_validate(data)
				except Exception:
					await websocket.send_json({"event": "error", "detail": "Invalid message payload"})
					continue

				try:
					async with AsyncSessionLocal() as db:
						msg = await send_chat_message(
							db,
							chat_id=chat_id,
							user_id=user_id,
							content=msg_in.content,
							message_type=msg_in.type,
						)
				except HTTPException as exc:
					await websocket.send_json({"event": "error", "detail": exc.detail})
					continue

				msg_out = chat_schemas.MessageResponse.model_validate(msg).model_dump(mode="json")
				delivered_user_ids = await chat_ws_manager.broadcast(
					chat_id=chat_id,
					message={"event": "message", "data": msg_out},
					exclude_user_id=user_id,
				)
				await websocket.send_json({"event": "message_ack", "data": msg_out})
				if delivered_user_ids:
					await websocket.send_json(
						{
							"event": "message_status",
							"data": {
								"message_id": msg_out.get("message_id"),
								"status": "delivered",
								"user_ids": sorted(delivered_user_ids),
							},
						}
					)
				continue

			if event == "typing":
				is_typing = False
				if isinstance(data, dict):
					is_typing = bool(data.get("is_typing", True))
				await chat_ws_manager.broadcast(
					chat_id=chat_id,
					message={"event": "typing", "data": {"user_id": user_id, "is_typing": is_typing}},
					exclude_user_id=user_id,
				)
				continue

			if event == "read":
				message_id = None
				if isinstance(data, dict):
					message_id = data.get("message_id")
				try:
					message_id_int = int(message_id)
				except Exception:
					await websocket.send_json({"event": "error", "detail": "Invalid read payload"})
					continue
				await chat_ws_manager.broadcast(
					chat_id=chat_id,
					message={
						"event": "message_status",
						"data": {"message_id": message_id_int, "status": "read", "user_id": user_id},
					},
				)
				continue

			if event == "ping":
				await websocket.send_json({"event": "pong"})
				continue

			await websocket.send_json({"event": "error", "detail": "Unknown event"})
	except WebSocketDisconnect:
		logger.info(f"WebSocket disconnected: user_id={user_id}, chat_id={chat_id}")
	except Exception as e:
		logger.error(f"WebSocket error: user_id={user_id}, chat_id={chat_id}, error={str(e)}")
	finally:
		user_still_online = await chat_ws_manager.disconnect(chat_id=chat_id, user_id=user_id, websocket=websocket)
		logger.info(f"WebSocket cleanup: user_id={user_id}, chat_id={chat_id}, still_online={user_still_online}")
		if not user_still_online:
			await chat_ws_manager.broadcast(
				chat_id=chat_id,
				message={"event": "presence", "data": {"user_id": user_id, "status": "offline"}},
				exclude_user_id=user_id,
			)
