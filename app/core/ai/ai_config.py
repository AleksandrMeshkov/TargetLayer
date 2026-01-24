import os
from typing import Dict, Any

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "30"))
AI_MODEL_NAME = os.getenv("AI_MODEL", "qwen2.5:3b")

MAX_RETRIES = 3
RETRY_DELAY = 1  

def validate_config() -> Dict[str, Any]:
    """Валидация конфигурации"""
    if OLLAMA_TIMEOUT < 10:
        raise ValueError("OLLAMA_TIMEOUT должен быть >= 10 секунд")
    if not OLLAMA_BASE_URL.startswith(("http://", "https://")):
        raise ValueError("OLLAMA_BASE_URL должен начинаться с http:// или https://")
    return {
        "base_url": OLLAMA_BASE_URL,
        "timeout": OLLAMA_TIMEOUT,
        "model": AI_MODEL_NAME,
        "max_retries": MAX_RETRIES
    }

SYSTEM_PROMPT = """Ты - планировщик целей. Пользователь ставит цель с дедлайном.
Твоя задача: разбить цель на конкретные задачи с четкими сроками.

Ответ ДОЛЖЕН быть валидным JSON (без ошибок синтаксиса):
{
  "goal_title": "Название цели",
  "goal_description": "Описание цели",
  "tasks": [
    {
      "title": "Название задачи 1",
      "description": "Конкретное описание что делать",
      "estimated_duration_days": 14,
      "deadline_offset_days": 30,
      "priority": "high",
      "resources": ["Ресурс 1", "Ресурс 2"]
    },
    {
      "title": "Название задачи 2",
      "description": "Конкретное описание что делать",
      "estimated_duration_days": 21,
      "deadline_offset_days": 60,
      "priority": "medium",
      "resources": ["Ресурс 3"]
    }
  ]
}

ПРАВИЛА ОБЯЗАТЕЛЬНЫ:
1. Ответ ТОЛЬКО JSON, без текста до и после
2. deadline_offset_days ВСЕГДА >= 0 и <=180
3. estimated_duration_days ВСЕГДА > 0
4. priority только: "high", "medium" или "low"
5. Все строки в двойных кавычках
6. Все запятые на месте
7. Нет trailing запятых
8. Распредели задачи равномерно по времени
9. Приоритеты: high - критически важные, medium - важные, low - второстепенные
10. Ресурсы должны быть конкретными (курсы, книги, инструменты)
11. БЕЗ ЛИШНЕГО ТЕКСТА. ТОЛЬКО JSON."""

GENERATION_CONFIG = {
    "temperature": 0.1,
    "num_predict": 1500,
    "repeat_penalty": 1.2,
}