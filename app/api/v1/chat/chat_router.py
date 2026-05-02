
from __future__ import annotations

import logging
from datetime import datetime

from fastapi import APIRouter, Depends, Path, Security, WebSocket, WebSocketDisconnect, status
from fastapi import HTTPException
from jwt import DecodeError
import jwt as pyjwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.websockets import WebSocketState

from app.core.database.database import AsyncSessionLocal, get_db
from app.core.security.jwt import JWTManager
from app.models.chat import Chat
from app.models.chat_participant import ChatParticipant
from app.models.message import Message
from app.models.user import User
from app.models.team_member import TeamMember
from app.schemas import chat as chat_schemas
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
	"""Создать групповой чат"""
	await _ensure_user_in_team(db, user_id=current_user.user_id, team_id=payload.team_id)
	
	normalized_ids = [int(uid) for uid in payload.participant_user_ids if uid is not None]
	participant_set = {current_user.user_id, *normalized_ids}
	
	if len(participant_set) < 2:
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail="Минимум 2 участника требуется",
		)
	
	members_stmt = select(TeamMember.user_id).where(TeamMember.team_id == payload.team_id)
	members_res = await db.execute(members_stmt)
	team_user_ids = set(members_res.scalars().all())
	
	if not participant_set.issubset(team_user_ids):
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail="Все участники должны быть в команде",
		)
	
	chat = Chat(team_id=payload.team_id, type="group", name=(payload.name or None))
	db.add(chat)
	await db.flush()
	
	for uid in sorted(participant_set):
		db.add(ChatParticipant(chat_id=chat.chat_id, user_id=uid, joined_at=datetime.utcnow()))
	
	await db.commit()
	await db.refresh(chat)
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
	"""Получить список моих чатов"""
	stmt = (
		select(Chat)
		.join(ChatParticipant, ChatParticipant.chat_id == Chat.chat_id)
		.where(ChatParticipant.user_id == current_user.user_id)
		.order_by(Chat.created_at.desc())
	)
	res = await db.execute(stmt)
	chats = list(res.scalars().unique().all())
	return chat_schemas.ChatListResponse(chats=chats, total=len(chats))


@router.post(
	"/team/{team_id}",
	response_model=chat_schemas.ChatResponse,
	openapi_extra={"security": [{"Bearer": []}]},
)
async def get_or_create_team_chat(
	team_id: int = Path(..., gt=0),
	current_user: User = Security(get_current_user),
	db: AsyncSession = Depends(get_db),
) -> Chat:
	"""Получить или создать общий командный чат"""
	await _ensure_user_in_team(db, user_id=current_user.user_id, team_id=team_id)
	
	existing_stmt = select(Chat).where(Chat.team_id == team_id, Chat.type == "team")
	existing_res = await db.execute(existing_stmt)
	existing = existing_res.scalar_one_or_none()
	
	if existing:
		participant_stmt = select(ChatParticipant.id).where(
			ChatParticipant.chat_id == existing.chat_id,
			ChatParticipant.user_id == current_user.user_id,
		)
		participant_res = await db.execute(participant_stmt)
		if participant_res.scalar_one_or_none() is None:
			db.add(ChatParticipant(chat_id=existing.chat_id, user_id=current_user.user_id, joined_at=datetime.utcnow()))
			await db.commit()
			await db.refresh(existing)
		return existing
	
	chat = Chat(team_id=team_id, type="team", name="Общий чат")
	db.add(chat)
	await db.flush()
	
	members_stmt = select(TeamMember.user_id).where(TeamMember.team_id == team_id)
	members_res = await db.execute(members_stmt)
	member_user_ids = list(members_res.scalars().all())
	for uid in member_user_ids:
		db.add(ChatParticipant(chat_id=chat.chat_id, user_id=uid, joined_at=datetime.utcnow()))
	
	await db.commit()
	await db.refresh(chat)
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
	"""Получить список участников чата"""
	await _ensure_user_is_chat_participant(db, chat_id=chat_id, user_id=current_user.user_id)
	stmt = select(ChatParticipant).where(ChatParticipant.chat_id == chat_id).order_by(ChatParticipant.joined_at.asc())
	res = await db.execute(stmt)
	participants = list(res.scalars().all())
	return chat_schemas.ChatParticipantsListResponse(participants=participants, total=len(participants))




async def _ensure_user_in_team(db: AsyncSession, *, user_id: int, team_id: int) -> None:
	"""Проверить, что пользователь состоит в команде"""
	stmt = select(TeamMember.id).where(
		TeamMember.team_id == team_id,
		TeamMember.user_id == user_id,
	)
	res = await db.execute(stmt)
	if res.scalar_one_or_none() is None:
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Пользователь не в команде")


async def _ensure_user_is_chat_participant(db: AsyncSession, *, chat_id: int, user_id: int) -> Chat:
	"""Проверить доступ к чату и вернуть объект чата"""
	stmt = select(Chat).where(Chat.chat_id == chat_id)
	res = await db.execute(stmt)
	chat = res.scalar_one_or_none()
	
	if not chat:
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Чат не найден")
	
	if chat.team_id:
		await _ensure_user_in_team(db, user_id=user_id, team_id=chat.team_id)
	
	stmt = select(ChatParticipant.id).where(
		ChatParticipant.chat_id == chat_id,
		ChatParticipant.user_id == user_id,
	)
	res = await db.execute(stmt)
	if res.scalar_one_or_none() is None:
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Доступ запрещен")
	
	return chat


@router.websocket("/{chat_id}/ws")
async def chat_websocket(
    websocket: WebSocket,
    chat_id: int,
) -> None:
    """WebSocket для чата: история, отправка, удаление сообщений, выход"""
    user_id: int | None = None
    
    # 🔥 ШАГ 1: Сначала принимаем соединение — ВСЕГДА первым!
    try:
        await websocket.accept()
    except RuntimeError:
        # Сокет уже закрыт (редко, но бывает при обрыве)
        logger.warning("WS already closed before accept: chat_id=%s", chat_id)
        return
    except Exception as e:
        logger.error("WS accept failed: %s", e, exc_info=True)
        return

    # 🔥 ШАГ 2: Теперь валидируем токен и авторизуем
    try:
        token = websocket.query_params.get("token")
        if not token:
            auth_header = websocket.headers.get("authorization")
            if auth_header and auth_header.lower().startswith("bearer "):
                token = auth_header.split(" ", 1)[1].strip() or None

        if not token:
            logger.info("WS auth failed: missing token (chat_id=%s)", chat_id)
            await websocket.send_json({"event": "error", "detail": "Требуется токен"})
            await websocket.close(code=4001, reason="Missing token")
            return

        sub = jwt_manager.verify_access_token(token)
        if not sub:
            logger.info("WS auth failed: invalid token (chat_id=%s)", chat_id)
            await websocket.send_json({"event": "error", "detail": "Неверный токен"})
            await websocket.close(code=4001, reason="Invalid token")
            return
        user_id = int(sub)
        
    except Exception as exc:
        # Логируем детали для отладки (без самого токена!)
        alg = token_type = exp = None
        try:
            if token:
                alg = pyjwt.get_unverified_header(token).get("alg")
                claims = pyjwt.decode(token, options={"verify_signature": False})
                token_type = claims.get("type")
                exp = claims.get("exp")
        except Exception:
            pass

        logger.warning(
            "WS auth exception: %s (%s) unverified={alg:%s,type:%s,exp:%s} chat_id=%s",
            exc.__class__.__name__, str(exc), alg, token_type, exp, chat_id,
            exc_info=True,
        )
        await websocket.send_json({"event": "error", "detail": "Ошибка авторизации"})
        await websocket.close(code=4001, reason="Auth error")
        return

    # 🔥 ШАГ 3: Проверяем доступ к чату
    async with AsyncSessionLocal() as db:
        try:
            await _ensure_user_is_chat_participant(db, chat_id=chat_id, user_id=user_id)
        except HTTPException as e:
            logger.info("WS access denied: chat_id=%s, user_id=%s, detail=%s", 
                       chat_id, user_id, e.detail)
            await websocket.send_json({"event": "error", "detail": e.detail})
            await websocket.close(code=4003, reason="Access denied")
            return

    # 🔥 ШАГ 4: Подключаем к менеджеру
    await chat_ws_manager.connect(chat_id=chat_id, user_id=user_id, websocket=websocket)
    logger.info("✅ WS connected: user=%s, chat=%s", user_id, chat_id)

    # 🔥 ШАГ 5: Отправляем историю
    try:
        async with AsyncSessionLocal() as db:
            stmt = (
                select(Message)
                .where(Message.chat_id == chat_id)
                .order_by(Message.created_at.asc())
            )
            res = await db.execute(stmt)
            messages = list(res.scalars().all())
            
            payload = [
                chat_schemas.MessageResponse.model_validate(m).model_dump(mode="json")
                for m in messages
            ]
            await websocket.send_json({"event": "history", "data": payload})
            logger.info("📤 Sent history: %d messages to chat=%s", len(payload), chat_id)
            
    except Exception as e:
        logger.error("❌ History send error: %s", e, exc_info=True)
        await websocket.send_json({"event": "error", "detail": "Ошибка загрузки истории"})
        # Не закрываем сокет — чат может работать без истории

    # 🔥 ШАГ 6: Отправляем участников
    try:
        async with AsyncSessionLocal() as db:
            stmt = select(ChatParticipant).where(ChatParticipant.chat_id == chat_id)
            res = await db.execute(stmt)
            participants = list(res.scalars().all())
            await websocket.send_json({
                "event": "participants",
                "data": [{"user_id": p.user_id, "joined_at": p.joined_at.isoformat()} 
                        for p in participants]
            })
    except Exception as e:
        logger.error("❌ Participants send error: %s", e, exc_info=True)

    # 🔥 ШАГ 7: Основной цикл обработки сообщений
    try:
        while True:
            data = await websocket.receive_json()
            action = data.get("action")

            if action == "send":
                content = (data.get("content") or "").strip()
                if not content:
                    await websocket.send_json({"event": "error", "detail": "Сообщение пустое"})
                    continue

                try:
                    async with AsyncSessionLocal() as db:
                        msg = Message(
                            chat_id=chat_id,
                            user_id=user_id,
                            type=data.get("type", "text"),
                            content=content,
                        )
                        db.add(msg)
                        await db.commit()
                        await db.refresh(msg)

                        msg_out = chat_schemas.MessageResponse.model_validate(msg).model_dump(mode="json")
                        await chat_ws_manager.broadcast(
                            chat_id=chat_id,
                            message={"event": "message", "data": msg_out},
                        )
                except Exception as e:
                    logger.error(f"Send error: {e}", exc_info=True)
                    await websocket.send_json({"event": "error", "detail": "Ошибка отправки"})

            elif action == "delete":
                message_id = data.get("message_id")
                try:
                    async with AsyncSessionLocal() as db:
                        stmt = select(Message).where(
                            Message.message_id == message_id,
                            Message.chat_id == chat_id,
                        )
                        res = await db.execute(stmt)
                        msg = res.scalar_one_or_none()
                        
                        if not msg:
                            await websocket.send_json({"event": "error", "detail": "Сообщение не найдено"})
                            continue
                        
                        if msg.user_id != user_id:
                            await websocket.send_json({"event": "error", "detail": "Может удалить только свое сообщение"})
                            continue
                        
                        await db.delete(msg)
                        await db.commit()
                        
                        await chat_ws_manager.broadcast(
                            chat_id=chat_id,
                            message={"event": "message_deleted", "data": {"message_id": message_id}},
                        )
                except Exception as e:
                    logger.error(f"Delete error: {e}", exc_info=True)
                    await websocket.send_json({"event": "error", "detail": "Ошибка удаления"})

            elif action == "leave":
                try:
                    async with AsyncSessionLocal() as db:
                        stmt = select(ChatParticipant).where(
                            ChatParticipant.chat_id == chat_id,
                            ChatParticipant.user_id == user_id,
                        )
                        res = await db.execute(stmt)
                        participant = res.scalar_one_or_none()
                        
                        if participant:
                            await db.delete(participant)
                            await db.commit()
                            
                            await chat_ws_manager.broadcast(
                                chat_id=chat_id,
                                message={"event": "user_left", "data": {"user_id": user_id}},
                            )
                except Exception as e:
                    logger.error(f"Leave error: {e}", exc_info=True)
                break

    except WebSocketDisconnect:
        logger.info("🔌 WS disconnected: user=%s, chat=%s", user_id, chat_id)
    except Exception as e:
        logger.error("💥 WS fatal error: %s", e, exc_info=True)
        try:
            if websocket.client_state == WebSocketState.CONNECTED:
                await websocket.send_json({"event": "error", "detail": "Критическая ошибка"})
        finally:
            await websocket.close(code=1011, reason="Internal error")
    finally:
        if user_id is not None:
            await chat_ws_manager.disconnect(chat_id=chat_id, user_id=user_id, websocket=websocket)
            logger.info("🔻 WS cleanup: user=%s, chat=%s", user_id, chat_id)