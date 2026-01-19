from fastapi import APIRouter, HTTPException, Depends, status
from app.services.ai_service import AIService, get_ai_service
from app.schemas.ai_schemas import AIChatResponse
import json
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/ai", tags=["AI"])


class GoalDecompositionRequest(BaseModel):
    goal: str
    timeframe: str | None = None


@router.get("/health")
async def health(ai_service: AIService = Depends(get_ai_service)):
    is_available = await ai_service.check_model_availability()
    status_code = 200 if is_available else 503
    return {
        "status": "healthy" if is_available else "unhealthy",
        "model": ai_service.model_name,
        "model_available": is_available
    }


@router.post("/decompose", response_model=AIChatResponse)
async def decompose_goal(
    request: GoalDecompositionRequest,
    ai_service: AIService = Depends(get_ai_service)
) -> AIChatResponse:
    is_available = await ai_service.check_model_availability()
    if not is_available:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model not available"
        )

    result = await ai_service.decompose_goal(request.goal, request.timeframe)

    if result.get("error"):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.get("message", "AI error")
        )

    # If service returned parsed JSON, serialize it as a string in the response field
    if result.get("json") is not None:
        resp_text = json.dumps(result.get("json"), ensure_ascii=False)
    else:
        resp_text = result.get("response", "")

    return AIChatResponse(
        response=resp_text,
        model=result.get("model")
    )
