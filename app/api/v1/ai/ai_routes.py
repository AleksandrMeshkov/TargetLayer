from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database.database import get_db
from app.services.ai_service.ai_service import get_ai_service, AIService
from app.services.ai_service.roadmap_service import RoadmapService
from app.schemas.ai_schemas import GoalDecompositionRequest
from app.services.user.get_my_user import get_current_user
from app.models.user import User

router = APIRouter(prefix="/ai", tags=["AI"])


@router.get("/health")
async def health_check(ai_service: AIService = Depends(get_ai_service)):
    is_healthy = await ai_service.check_health()
    return {
        "status": "healthy" if is_healthy else "unhealthy",
        "model": ai_service.model_name,
        "available": is_healthy
    }


@router.post("/decompose")
async def decompose(
    request: GoalDecompositionRequest,
    ai_service: AIService = Depends(get_ai_service)
):
    if not await ai_service.check_health():
        raise HTTPException(status_code=503, detail="AI unavailable")
    
    result = await ai_service.decompose_goal(request)
    
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result.get("error"))
    
    return result


@router.post("/create-roadmap", openapi_extra={"security": [{"Bearer": []}]})
async def create_roadmap(
    request: GoalDecompositionRequest,
    db: AsyncSession = Depends(get_db),
    ai_service: AIService = Depends(get_ai_service),
    current_user: User = Depends(get_current_user)
):
    if not await ai_service.check_health():
        raise HTTPException(status_code=503, detail="AI unavailable")
    
    ai_result = await ai_service.decompose_goal(request)
    
    if not ai_result["success"]:
        raise HTTPException(status_code=500, detail=ai_result.get("error"))
    
    service = RoadmapService(db)
    goal = await service.create_from_ai(ai_result["data"], user_id=int(current_user.user_id))
    
    return {
        "success": True,
        "goal_id": goal.goals_id,
        "title": goal.title,
        "tasks": len(ai_result["data"].tasks),
        "tokens": ai_result.get("tokens"),
        "time": ai_result.get("time")
    }
