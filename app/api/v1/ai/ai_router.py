from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
from typing import Optional

from app.core.database.database import get_db
from app.services.ai_service.ai_helth import check_ai_health
from app.services.ai_service.ai_chat_roadmap import ai_service
from app.services.user.get_my_user import get_current_user, get_optional_user
from app.models.user import User
from app.models.goal import Goal
from app.models.roadmap import Roadmap
from app.models.task import Task
from app.schemas.ai_schemas import AIRoadmapRequest, AIRoadmapResponse, RoadmapSaveRequest


router = APIRouter(prefix="/ai", tags=["ai"])


@router.get("/health", summary="Проверка доступности AI-сервиса")
async def ai_health():
    return await check_ai_health()


@router.post("/chat", response_model=AIRoadmapResponse, summary="Генерация roadmap от AI")
async def ai_chat(
    request: AIRoadmapRequest,
    current_user: Optional[User] = Depends(get_optional_user),
):
   
    try:
        result = await ai_service.chat(request.prompt)
        return AIRoadmapResponse(**result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"AI parsing error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AI service error: {str(e)}"
        )


@router.post(
    "/save-roadmap", 
    response_model=dict, 
    status_code=status.HTTP_201_CREATED,
    openapi_extra={"security": [{"Bearer": []}]}
)
async def save_roadmap(
    request: RoadmapSaveRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        goal = Goal(
            user_id=current_user.user_id,
            title=request.goal_title,
            description=request.goal_description,
            created_at=datetime.utcnow()
        )
        db.add(goal)
        await db.flush()  

        roadmap = Roadmap(
            goals_id=goal.goals_id,
            completed=False,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(roadmap)
        await db.flush()  

        for task_data in request.tasks:
            deadline_end = None
            if task_data.deadline_offset_days is not None:
                deadline_end = datetime.utcnow() + timedelta(days=task_data.deadline_offset_days)

            task = Task(
                roadmap_id=roadmap.roadmap_id,
                title=task_data.title,
                description=task_data.description,
                order_index=task_data.order_index or 0,
                completed=False,
                deadline_start=datetime.utcnow(),
                deadline_end=deadline_end,
                created_at=datetime.utcnow()
            )
            db.add(task)

        await db.commit()

        return {
            "status": "success",
            "goal_id": goal.goals_id,
            "roadmap_id": roadmap.roadmap_id,
            "tasks_count": len(request.tasks)
        }

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save roadmap: {str(e)}"
        )