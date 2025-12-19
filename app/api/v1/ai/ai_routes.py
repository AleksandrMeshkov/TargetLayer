from fastapi import APIRouter, HTTPException, Depends, status, Query
from app.services.ai_service import AIService, get_ai_service
from app.schemas.ai_schemas import (
    AIChatRequest,
    AIChatResponse,
    AIHealthCheck,
    GoalDecompositionRequest,
    GoalDecompositionResponse
)
from app.core.ai.ai_helpers import QuickResponseMode, optimizer, response_cache

router = APIRouter(
    prefix="/api/v1/ai",
    tags=["AI - Tinyllama Model"],
    responses={
        500: {"description": "Internal Server Error"},
        503: {"description": "Service Unavailable"}
    }
)


@router.get(
    "/health",
    response_model=AIHealthCheck,
    summary="Проверка статуса AI сервиса",
)
async def health_check(ai_service: AIService = Depends(get_ai_service)) -> AIHealthCheck:
    try:
        is_available = await ai_service.check_model_availability()
        
        if is_available:
            return AIHealthCheck(
                status="healthy",
                model_available=True,
                model_name=ai_service.model_name,
                message="AI сервис работает нормально"
            )
        else:
            return AIHealthCheck(
                status="unhealthy",
                model_available=False,
                model_name=ai_service.model_name,
                message=f"Модель {ai_service.model_name} не доступна. Запусти: ollama run {ai_service.model_name}"
            )
    except Exception as e:
        return AIHealthCheck(
            status="unhealthy",
            model_available=False,
            message=f"Ошибка подключения: {str(e)}"
        )


@router.post(
    "/chat",
    response_model=AIChatResponse,
    summary="Чат с AI моделью",
)
async def chat(
    request: AIChatRequest,
    mode: str = Query("balanced", description="quick|balanced|detailed"),
    ai_service: AIService = Depends(get_ai_service)
) -> AIChatResponse:
    try:
        mode_config = QuickResponseMode.get_config(mode)
        
        cache_key = response_cache.generate_key(
            request.message,
            request.temperature or mode_config["temperature"],
            request.max_tokens or mode_config["max_tokens"]
        )
        cached_response = response_cache.get(cache_key)
        if cached_response:
            cached_response["cached"] = True
            return AIChatResponse(**cached_response)
        
        is_available = await ai_service.check_model_availability()
        if not is_available:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Модель {ai_service.model_name} недоступна. Запусти Ollama: ollama run {ai_service.model_name}"
            )

        temp = request.temperature or mode_config["temperature"]
        tokens = request.max_tokens or mode_config["max_tokens"]
        
        result = await ai_service.chat(
            message=request.message,
            context=request.context,
            temperature=temp,
            max_tokens=tokens
        )

        if result.get("error"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("message", "Unknown error")
            )

        response_data = {
            "response": result["response"],
            "tokens_used": result.get("tokens_used"),
            "processing_time": result.get("processing_time"),
            "model": result.get("model"),
            "cached": False
        }
        
        response_cache.set(cache_key, response_data)
        
        return AIChatResponse(**response_data)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.post(
    "/decompose-goal",
    response_model=AIChatResponse,
    summary="Разложение цели на подцели",
)
async def decompose_goal(
    request: GoalDecompositionRequest,
    ai_service: AIService = Depends(get_ai_service)
) -> AIChatResponse:
    try:
        is_available = await ai_service.check_model_availability()
        if not is_available:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Модель недоступна"
            )

        result = await ai_service.decompose_goal(
            goal=request.goal,
            timeframe=request.timeframe,
            additional_info=request.additional_info
        )

        if result.get("error"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("message")
            )

        return AIChatResponse(
            response=result["response"],
            tokens_used=result.get("tokens_used"),
            processing_time=result.get("processing_time"),
            model=result.get("model")
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post(
    "/generate-tasks",
    response_model=AIChatResponse,
    summary="Генерирование списка задач",
)
async def generate_tasks(
    project_description: str,
    priority: str = "medium",
    ai_service: AIService = Depends(get_ai_service)
) -> AIChatResponse:
    try:
        is_available = await ai_service.check_model_availability()
        if not is_available:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI модель недоступна"
            )

        result = await ai_service.generate_tasks(
            project_description=project_description,
            priority_level=priority
        )

        if result.get("error"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("message")
            )

        return AIChatResponse(
            response=result["response"],
            tokens_used=result.get("tokens_used"),
            processing_time=result.get("processing_time"),
            model=result.get("model")
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post(
    "/analyze",
    response_model=AIChatResponse,
    summary="Анализ контента",
)
async def analyze(
    content: str,
    analysis_type: str = "general",
    ai_service: AIService = Depends(get_ai_service)
) -> AIChatResponse:
    try:
        is_available = await ai_service.check_model_availability()
        if not is_available:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI модель недоступна"
            )

        result = await ai_service.analyze(
            content=content,
            analysis_type=analysis_type
        )

        if result.get("error"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("message")
            )

        return AIChatResponse(
            response=result["response"],
            tokens_used=result.get("tokens_used"),
            processing_time=result.get("processing_time"),
            model=result.get("model")
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get(
    "/model-info",
    summary="Информация о модели",
)
async def model_info(ai_service: AIService = Depends(get_ai_service)):
    try:
        info = await ai_service.get_model_info()
        return {
            "model": ai_service.model_name,
            "details": info
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
