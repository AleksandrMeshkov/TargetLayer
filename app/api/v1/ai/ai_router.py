from fastapi import APIRouter, Depends, HTTPException, status, Security
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
import json
from typing import Optional

from app.core.database.database import get_db
from app.services.ai_service.ai_helth import check_ai_health
from app.services.ai_service.ai_chat_roadmap import ai_service
from app.services.ai_service.ai_history import save_chat, fetch_history, create_conversation
from app.services.user.get_my_user import get_current_user, get_optional_user
from app.models.user import User
from app.models.goal import Goal
from app.models.roadmap import Roadmap
from app.models.task import Task
from app.schemas.ai_schemas import AIRoadmapRequest, AIRoadmapResponse, RoadmapSaveRequest


router = APIRouter(prefix="/ai", tags=["ai"])

@router.get("/health", summary="Проверка доступности AI-сервиса")
async def ai_health(
):
    return await check_ai_health()

@router.post(
    "/chat", 
    response_model=AIRoadmapResponse, 
    summary="Генерация roadmap от AI",
    openapi_extra={"security": [{"Bearer": []}]}
)
async def ai_chat(
    request: AIRoadmapRequest,
    current_user: User = Security(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        result = await ai_service.chat(request.prompt)
        try:
            ai_text = json.dumps(result, ensure_ascii=False)
        except Exception:
            ai_text = str(result)

        conv_id = None
        if getattr(request, "conversation_id", None):
            conv_id = request.conversation_id
        try:
            goal = Goal(user_id=current_user.user_id, title=result.get("goal_title"), description=result.get("goal_description"))
            db.add(goal)
            await db.flush()

            roadmap = Roadmap(goals_id=goal.goals_id)
            db.add(roadmap)
            await db.flush()

            tasks = result.get("tasks", [])
            for idx, t in enumerate(tasks):
                title = t.get("title")
                description = t.get("description")
                order_index = t.get("order_index") if t.get("order_index") is not None else idx
                deadline_offset = t.get("deadline_offset_days")
                if deadline_offset is not None:
                    deadline_start = datetime.utcnow()
                    deadline_end = datetime.utcnow() + timedelta(days=int(deadline_offset))
                else:
                    deadline_start = None
                    deadline_end = None

                task = Task(
                    roadmap_id=roadmap.roadmap_id,
                    title=title,
                    description=description,
                    order_index=order_index,
                    deadline_start=deadline_start,
                    deadline_end=deadline_end,
                )
                db.add(task)

            await db.commit()
        except Exception:
            await db.rollback()
            raise

        await save_chat(db, current_user.user_id, request.prompt, ai_text, conversation_id=conv_id)
        return AIRoadmapResponse(**result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"AI parsing error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service temporarily unavailable"
        )


@router.get("/history", summary="История переписки с AI", openapi_extra={"security": [{"Bearer": []}]})
async def ai_get_history(
    current_user: User = Security(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    history = await fetch_history(db, current_user.user_id)
    return history


@router.post("/conversations", summary="Создать новый чат", openapi_extra={"security": [{"Bearer": []}]})
async def ai_create_conversation(
    current_user: User = Security(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    conversation_id = await create_conversation(db, current_user.user_id)
    return {"conversation_id": conversation_id}


@router.get("/conversations", summary="Список чатов пользователя", openapi_extra={"security": [{"Bearer": []}]})
async def ai_list_conversations(
    current_user: User = Security(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    history = await fetch_history(db, current_user.user_id)
    return [
        {"conversation_id": c["conversation_id"], "created_at": c["created_at"], "updated_at": c["updated_at"]}
        for c in history
    ]