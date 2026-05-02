from fastapi import APIRouter, Depends, HTTPException, status, Security
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
import json
from typing import Optional

from app.core.database.database import get_db
from app.services.ai_service.ai_helth import check_ai_health
from app.services.ai_service.ai_chat_roadmap import ai_service
from app.services.ai_service.ai_history import save_chat, fetch_history, create_conversation
from app.services.ai_service.delite_history_in_chat import delete_ai_conversation
from app.services.user.get_my_user import get_current_user, get_optional_user
from app.models.user import User
from sqlalchemy import select
from app.models.goal import Goal
from app.models.roadmap import Roadmap
from app.models.roadmap_access import RoadmapAccess
from app.models.task import Task
from app.models.team import Team
from app.models.team_role import TeamRole
from app.models.team_member import TeamMember
from app.schemas.ai_schemas import AIRoadmapRequest, AIRoadmapResponse, RoadmapSaveRequest


router = APIRouter(prefix="/api/v1/ai", tags=["ai"])

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

        goal = Goal(
            user_id=current_user.user_id,
            title=result.get("goal_title"),
            description=result.get("goal_description"),
        )
        db.add(goal)
        await db.flush()

        roadmap = Roadmap(team_id=None, goals_id=goal.goals_id, completed=False)
        db.add(roadmap)
        await db.flush()

        access = RoadmapAccess(
            roadmap_id=roadmap.roadmap_id,
            user_id=current_user.user_id,
            permission="owner",
        )
        db.add(access)

        tasks = result.get("tasks", [])
        for idx, t in enumerate(tasks):
            title = t.get("title")
            description = t.get("description")
            order_index = t.get("order_index") if t.get("order_index") is not None else idx
            task = Task(
                roadmap_id=roadmap.roadmap_id,
                title=title,
                description=description,
                order_index=order_index,
            )
            db.add(task)


        await db.commit()
        await save_chat(db, current_user.user_id, request.prompt, ai_text, conversation_id=conv_id)
        return AIRoadmapResponse(**result)
    except Exception:
        await db.rollback()
        raise
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


@router.delete(
	"/conversations/{conversation_id}",
	summary="Удалить чат с AI",
	openapi_extra={"security": [{"Bearer": []}]},
)
async def ai_delete_conversation(
	conversation_id: int,
	current_user: User = Security(get_current_user),
	db: AsyncSession = Depends(get_db),
):
	return await delete_ai_conversation(db, current_user.user_id, conversation_id)