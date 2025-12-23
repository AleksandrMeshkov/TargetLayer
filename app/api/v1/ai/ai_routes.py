from fastapi import APIRouter, HTTPException, Depends, status, Query
from app.services.ai_service import AIService, get_ai_service
from app.schemas.ai_schemas import (
    AIChatRequest,
    AIChatResponse,
    AIHealthCheck,
    GoalDecompositionRequest,
    GoalDecompositionResponse,
    RoadmapRequest  # Добавьте этот импорт
)
from app.core.ai.ai_helpers import optimizer, response_cache

router = APIRouter(
    prefix="/api/v1/ai",
    tags=["AI - Ollama Model"],
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
        # Mode-based config for response parameters
        mode_configs = {
            "quick": {"max_tokens": 256, "temperature": 0.3},
            "balanced": {"max_tokens": 512, "temperature": 0.6},
            "detailed": {"max_tokens": 2048, "temperature": 0.7},
        }
        mode_config = mode_configs.get(mode, mode_configs["balanced"])
        
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

# ДОБАВЬТЕ ЭТОТ НОВЫЙ ЭНДПОИНТ ДЛЯ ГЕНЕРАЦИИ РОАДМАПОВ
@router.post(
    "/generate-roadmap",
    response_model=AIChatResponse,
    summary="Генерация роадмапа для цели",
)
async def generate_roadmap(
    goal: str = Query(..., description="Цель пользователя"),
    timeframe: str = Query(..., description="Временные рамки (например: '6 месяцев')"),
    current_level: str = Query(None, description="Текущий уровень (например: 'новичок')"),
    available_time: str = Query(None, description="Доступное время в день/неделю"),
    preferences: str = Query(None, description="Предпочтения пользователя через запятую"),
    ai_service: AIService = Depends(get_ai_service)
) -> AIChatResponse:
    try:
        is_available = await ai_service.check_model_availability()
        if not is_available:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Модель {ai_service.model_name} недоступна"
            )

        # Преобразуем строку предпочтений в список
        preferences_list = None
        if preferences:
            preferences_list = [p.strip() for p in preferences.split(',')]

        result = await ai_service.generate_roadmap(
            goal=goal,
            timeframe=timeframe,
            current_level=current_level,
            available_time=available_time,
            preferences=preferences_list
        )

        if result.get("error"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("message")
            )

        return AIChatResponse(
            response=result["roadmap"],  # Используем roadmap вместо response
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

# ДОБАВЬТЕ ЭТОТ ЭНДПОИНТ ДЛЯ ПАРСИНГА ЗАДАЧ ИЗ РОАДМАПА
@router.post(
    "/parse-roadmap-tasks",
    summary="Парсинг задач из роадмапа",
)
async def parse_roadmap_tasks(
    roadmap_text: str,
    ai_service: AIService = Depends(get_ai_service)
):
    """Парсит задачи из текста роадмапа в структурированный формат"""
    try:
        tasks = ai_service._extract_tasks_from_roadmap(roadmap_text)
        structured = ai_service._structure_tasks_for_db(tasks)
        
        return {
            "total_tasks": len(tasks),
            "tasks": tasks,
            "structured_tasks": structured,
            "stages": list(set([t['stage'] for t in tasks if t['stage']]))
        }
        
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
