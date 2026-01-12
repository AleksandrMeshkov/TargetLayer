from fastapi import APIRouter, HTTPException, Depends, status
from app.services.ai_service import AIService, get_ai_service
from app.schemas.ai_schemas import AIChatRequest, AIChatResponse, AIHealthCheck

router = APIRouter(prefix="/api/v1/ai", tags=["AI"])


@router.get("/health", response_model=AIHealthCheck)
async def health(ai_service: AIService = Depends(get_ai_service)) -> AIHealthCheck:
    is_available = await ai_service.check_model_availability()
    if is_available:
        return AIHealthCheck(status="healthy", model_available=True, model_name=ai_service.model_name, message="Model is available")
    return AIHealthCheck(status="unhealthy", model_available=False, model_name=ai_service.model_name, message="Model not available")


@router.post("/generate", response_model=AIChatResponse)
async def generate(request: AIChatRequest, ai_service: AIService = Depends(get_ai_service)) -> AIChatResponse:
    is_available = await ai_service.check_model_availability()
    if not is_available:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Model not available")

    result = await ai_service.chat(
        message=request.message,
        context=request.context,
        temperature=request.temperature,
        max_tokens=request.max_tokens,
    )

    if result.get("error"):
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=result.get("message", "AI error"))

    return AIChatResponse(
        response=result.get("response", ""),
        tokens_used=result.get("tokens_used"),
        processing_time=result.get("processing_time"),
        model=result.get("model"),
        cached=result.get("cached", False),
    )
