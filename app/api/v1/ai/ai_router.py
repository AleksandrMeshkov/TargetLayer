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