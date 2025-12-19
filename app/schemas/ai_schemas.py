from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ChatMessage(BaseModel):
    """Модель сообщения в чате"""
    role: str = Field(..., description="Роль: 'user', 'assistant' или 'system'")
    content: str = Field(..., description="Содержание сообщения", min_length=1, max_length=10000)

    class Config:
        json_schema_extra = {
            "example": {
                "role": "user",
                "content": "Помоги мне разложить мою цель на подцели"
            }
        }


class AIChatRequest(BaseModel):
    """Запрос к AI для обработки"""
    message: str = Field(..., description="Сообщение пользователя", min_length=1, max_length=10000)
    context: Optional[List[ChatMessage]] = Field(
        default=None, 
        description="История сообщений (максимум 20)",
        max_length=20
    )
    temperature: Optional[float] = Field(
        default=0.7, 
        description="Температура генерации (0.0-1.0)", 
        ge=0.0, 
        le=1.0
    )
    max_tokens: Optional[int] = Field(
        default=1024, 
        description="Максимум токенов в ответе",
        ge=1,
        le=4096
    )
    task_type: Optional[str] = Field(
        default="chat",
        description="Тип задачи: chat, decompose_goal, generate_tasks, analyze",
        pattern="^(chat|decompose_goal|generate_tasks|analyze)$"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Я хочу выучить английский язык в течение 6 месяцев",
                "temperature": 0.7,
                "max_tokens": 1024,
                "task_type": "decompose_goal"
            }
        }


class AIChatResponse(BaseModel):
    """Ответ от AI"""
    response: str = Field(..., description="Ответ модели")
    tokens_used: Optional[int] = Field(None, description="Количество использованных токенов")
    processing_time: Optional[float] = Field(None, description="Время обработки в секундах")
    model: Optional[str] = Field(None, description="Название используемой модели")
    cached: bool = Field(default=False, description="Был ли ответ из кеша")

    class Config:
        json_schema_extra = {
            "example": {
                "response": "Отличная цель! Вот план разложения...",
                "tokens_used": 256,
                "processing_time": 2.3,
                "model": "phi3:mini",
                "cached": False
            }
        }


class AIHealthCheck(BaseModel):
    status: str = Field(..., description="Статус: 'healthy' или 'unhealthy'")
    model_available: bool = Field(..., description="Доступна ли модель")
    model_name: Optional[str] = Field(None, description="Название модели")
    message: Optional[str] = Field(None, description="Дополнительная информация")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "model_available": True,
                "model_name": "tinyllama",
                "message": "AI сервис работает нормально"
            }
        }


class AIError(BaseModel):
    error: str = Field(..., description="Название ошибки")
    message: str = Field(..., description="Описание ошибки")
    details: Optional[str] = Field(None, description="Дополнительная информация")

    class Config:
        json_schema_extra = {
            "example": {
                "error": "MODEL_NOT_AVAILABLE",
                "message": "Модель недоступна",
                "details": "Убедись, что Ollama запущен"
            }
        }


class GoalDecompositionRequest(BaseModel):
    goal: str = Field(..., description="Главная цель", min_length=5, max_length=500)
    timeframe: Optional[str] = Field(None, description="Временные рамки (напр. '3 месяца')")
    additional_info: Optional[str] = Field(None, description="Дополнительная информация")

    class Config:
        json_schema_extra = {
            "example": {
                "goal": "Выучить Python для разработки веб-приложений",
                "timeframe": "6 месяцев",
                "additional_info": "Я новичок в программировании"
            }
        }


class GoalDecompositionResponse(BaseModel):
    main_goal: str = Field(..., description="Исходная цель")
    subgoals: List[str] = Field(..., description="Список подцелей")
    action_items: dict = Field(..., description="Действия для каждой подцели")
    timeline: Optional[dict] = Field(None, description="Временная шкала")
    metrics: Optional[List[str]] = Field(None, description="Метрики прогресса")

    class Config:
        json_schema_extra = {
            "example": {
                "main_goal": "Выучить Python",
                "subgoals": ["Основы синтаксиса", "ООП", "Web-фреймворки"],
                "action_items": {
                    "Основы синтаксиса": ["Пройти курс", "Решить 10 задач"]
                },
                "timeline": {"Основы": "2 месяца"},
                "metrics": ["Количество решенных задач", "Проекты"]
            }
        }


class AIModelInfo(BaseModel):
    name: str = Field(..., description="Название модели")
    parameters: str = Field(..., description="Количество параметров")
    context_window: int = Field(..., description="Размер контекста")
    max_tokens_per_request: int = Field(..., description="Макс токенов на запрос")
    supported_languages: List[str] = Field(..., description="Поддерживаемые языки")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "phi3:mini",
                "parameters": "3.8B",
                "context_window": 4096,
                "max_tokens_per_request": 4096,
                "supported_languages": ["en", "ru"]
            }
        }
