from fastapi import APIRouter, Depends, HTTPException, status, Security
from sqlalchemy.ext.asyncio import AsyncSession
import json
import re

from app.core.database.database import get_db
from app.services.ai_service.ai_helth import check_ai_health
from app.services.ai_service.ai_chat_roadmap import ai_service
from app.services.ai_service.ai_history import save_chat, fetch_history, create_conversation
from app.services.ai_service.delite_history_in_chat import delete_ai_conversation
from app.services.user.get_my_user import get_current_user
from app.models.user import User
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models.ai_conversation import AIConversation
from app.models.goal import Goal
from app.models.roadmap import Roadmap
from app.models.task import Task
from app.schemas.ai_schemas import AIRoadmapRequest, AIRoadmapResponse, RoadmapSaveRequest


router = APIRouter(prefix="/api/v1/ai", tags=["ai"])


def _extract_deadline_days(prompt: str) -> int | None:
    text = prompt.lower()

    patterns = [
        (r"(\d+)\s*(?:дн(?:я|ей)?|день|дня)", 1),
        (r"(\d+)\s*(?:недел(?:я|и|ь))", 7),
        (r"(\d+)\s*(?:месяц(?:а|ев)?|мес\.)", 30),
        (r"(\d+)\s*(?:час(?:а|ов)?)", 1),
    ]

    for pattern, multiplier in patterns:
        match = re.search(pattern, text)
        if match:
            value = int(match.group(1)) * multiplier
            return max(value, 1)

    return None

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
        conversation_history = None
        current_roadmap_context = None
        conversation = None
        max_deadline_days = _extract_deadline_days(request.prompt)

        if request.conversation_id is not None:
            conversation_stmt = select(AIConversation).where(
                AIConversation.conversation_id == request.conversation_id,
                AIConversation.user_id == current_user.user_id,
            )
            conversation_result = await db.execute(conversation_stmt)
            conversation = conversation_result.scalar_one_or_none()
            if conversation is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Conversation не найден",
                )

            history = await fetch_history(db, current_user.user_id)
            for conv in history:
                if conv["conversation_id"] == request.conversation_id:
                    conversation_history = [
                        {"role": msg["role"], "content": msg["content"]}
                        for msg in conv["messages"]
                    ]
                    break

            if conversation.active_roadmap_id is not None:
                roadmap_stmt = (
                    select(Roadmap)
                    .options(selectinload(Roadmap.goal), selectinload(Roadmap.tasks))
                    .where(Roadmap.roadmap_id == conversation.active_roadmap_id)
                )
                roadmap_result = await db.execute(roadmap_stmt)
                roadmap = roadmap_result.scalar_one_or_none()
                if roadmap is not None:
                    current_roadmap_context = {
                        "roadmap_id": roadmap.roadmap_id,
                        "goals_id": roadmap.goals_id,
                        "goal_title": roadmap.goal.title if roadmap.goal else "",
                        "goal_description": roadmap.goal.description if roadmap.goal else None,
                        "created_at": roadmap.created_at.isoformat() if roadmap.created_at else None,
                        "tasks": [
                            {
                                "task_id": task.task_id,
                                "title": task.title,
                                "description": task.description,
                                "order_index": task.order_index,
                            }
                            for task in sorted(roadmap.tasks, key=lambda item: item.order_index)
                        ],
                    }

        result = await ai_service.chat(
            request.prompt,
            conversation_history=conversation_history,
            current_roadmap_context=current_roadmap_context,
            max_deadline_days=max_deadline_days,
        )

        try:
            ai_text = json.dumps(result, ensure_ascii=False)
        except Exception:
            ai_text = str(result)

        active_goal_id = None
        active_roadmap_id = None

        if conversation is not None and conversation.active_roadmap_id is not None:
            roadmap = await db.get(Roadmap, conversation.active_roadmap_id)
            if roadmap is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Active roadmap not found",
                )

            goal = await db.get(Goal, roadmap.goals_id)
            if goal is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Active goal not found",
                )

            goal.title = result.get("goal_title", goal.title)
            goal.description = result.get("goal_description", goal.description)

            existing_tasks_stmt = select(Task).where(Task.roadmap_id == roadmap.roadmap_id)
            existing_tasks_result = await db.execute(existing_tasks_stmt)
            for existing_task in existing_tasks_result.scalars().all():
                await db.delete(existing_task)

            for idx, task_data in enumerate(result.get("tasks", [])):
                db.add(
                    Task(
                        roadmap_id=roadmap.roadmap_id,
                        title=task_data.get("title"),
                        description=task_data.get("description"),
                        order_index=task_data.get("order_index") if task_data.get("order_index") is not None else idx,
                    )
                )

            active_goal_id = goal.goals_id
            active_roadmap_id = roadmap.roadmap_id
        else:
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

            active_goal_id = goal.goals_id
            active_roadmap_id = roadmap.roadmap_id

        await save_chat(
            db,
            current_user.user_id,
            request.prompt,
            ai_text,
            conversation_id=request.conversation_id,
            active_goal_id=active_goal_id,
            active_roadmap_id=active_roadmap_id,
        )
        await db.commit()
        return AIRoadmapResponse(**result)
    except ValueError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка синтаксического анализа искусственного интеллекта: {str(e)}"
        )
    except HTTPException:
        await db.rollback()
        raise
    except Exception:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Сервис искусственного интеллекта временно недоступен"
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