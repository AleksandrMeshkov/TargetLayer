"""AI service module with provider selection.

Supports two providers:
- 'ollama': REST API via Docker/local Ollama server (recommended for tinyllama in Docker)
- 'tinyllama': Local llama_cpp binding (requires llama-cpp-python and model file)

Configure via settings.AI_PROVIDER and set appropriate env vars.
"""

import httpx
import logging
import time
from typing import Optional, List, Dict

from app.core.settings.settings import settings
from app.core.ai.ai_config import (
    SYSTEM_PROMPT_CHAT,
    SYSTEM_PROMPT_GOAL_DECOMPOSITION,
    SYSTEM_PROMPT_TASK_GENERATION,
    SYSTEM_PROMPT_ANALYSIS,
    OLLAMA_CONNECTION_TIMEOUT,
    ERRORS,
)
from app.schemas.ai_schemas import ChatMessage

logger = logging.getLogger(__name__)


class AIService:
    """Ollama-based AI service (REST API via HTTP)."""

    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL
        self.model_name = settings.AI_MODEL_NAME
        self.default_temperature = settings.AI_TEMPERATURE
        self.default_max_tokens = settings.AI_MAX_TOKENS
        timeout_value = settings.OLLAMA_TIMEOUT
        self.timeout = httpx.Timeout(
            timeout=timeout_value,
            connect=OLLAMA_CONNECTION_TIMEOUT,
            read=timeout_value,
        )

    async def check_model_availability(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                if response.status_code == 200:
                    data = response.json()
                    models = [m.get("name") for m in data.get("models", [])]
                    is_available = self.model_name in models
                    if not is_available:
                        logger.warning(f"Model {self.model_name} not found. Available: {models}")
                    return is_available
                return False
        except Exception as e:
            logger.error(f"Error checking model availability: {e}")
            return False

    async def chat(
        self,
        message: str,
        context: Optional[List[ChatMessage]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None,
    ) -> Dict:
        try:
            temperature = temperature if temperature is not None else self.default_temperature
            max_tokens = max_tokens if max_tokens is not None else min(1024, self.default_max_tokens)
            system_prompt = system_prompt or SYSTEM_PROMPT_CHAT

            messages = self._prepare_messages(message, context, system_prompt)

            start_time = time.time()
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json={
                        "model": self.model_name,
                        "messages": messages,
                        "temperature": temperature,
                        "stream": False,
                        "options": {"num_predict": max_tokens},
                    },
                )

            processing_time = time.time() - start_time

            if response.status_code != 200:
                logger.error(f"AI API error: {response.status_code} - {response.text}")
                return {
                    "error": True,
                    "message": ERRORS.get("SERVER_ERROR", "Unknown error"),
                    "status_code": response.status_code,
                }

            result = response.json()

            return {
                "error": False,
                "response": result.get("message", {}).get("content", ""),
                "tokens_used": result.get("eval_count", 0),
                "processing_time": processing_time,
                "model": self.model_name,
                "cached": False,
            }

        except httpx.TimeoutException:
            logger.error("AI request timeout")
            return {"error": True, "message": ERRORS.get("TIMEOUT", "Request timeout")}
        except httpx.ConnectError:
            logger.error(f"Cannot connect to Ollama server at {self.base_url}")
            return {"error": True, "message": ERRORS.get("CONNECTION_ERROR", "Connection error")}
        except Exception as e:
            logger.error(f"Unexpected error in AI service: {e}")
            return {"error": True, "message": ERRORS.get("SERVER_ERROR", "Unknown error"), "details": str(e)}

    async def decompose_goal(self, goal: str, timeframe: Optional[str] = None, additional_info: Optional[str] = None) -> Dict:
        prompt = f"Разложи следующую цель на подцели и действия:\n\n"
        prompt += f"Цель: {goal}\n"
        if timeframe:
            prompt += f"Временные рамки: {timeframe}\n"
        if additional_info:
            prompt += f"Дополнительно: {additional_info}\n"
        prompt += "\nПредоставь структурированный ответ с подцелями, действиями и временной шкалой."

        result = await self.chat(message=prompt, temperature=0.7, max_tokens=2048, system_prompt=SYSTEM_PROMPT_GOAL_DECOMPOSITION)
        return result

    async def generate_tasks(self, project_description: str, priority_level: str = "medium") -> Dict:
        prompt = f"Создай детальный список задач для следующего проекта:\n\n{project_description}"
        if priority_level:
            prompt += f"\nУровень приоритета: {priority_level}"

        result = await self.chat(message=prompt, temperature=0.6, max_tokens=2048, system_prompt=SYSTEM_PROMPT_TASK_GENERATION)
        return result

    async def analyze(self, content: str, analysis_type: str = "general") -> Dict:
        prompt = f"Проанализируй следующее {analysis_type}:\n\n{content}"
        result = await self.chat(message=prompt, temperature=0.5, max_tokens=2048, system_prompt=SYSTEM_PROMPT_ANALYSIS)
        return result

    def _prepare_messages(self, message: str, context: Optional[List[ChatMessage]] = None, system_prompt: Optional[str] = None) -> List[Dict]:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        if context:
            for msg in context[-20:]:
                messages.append({"role": msg.role, "content": msg.content})
        messages.append({"role": "user", "content": message})
        return messages

    async def get_model_info(self) -> Dict:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(f"{self.base_url}/api/show", json={"name": self.model_name})
            if response.status_code == 200:
                return response.json()
            return {"error": "Could not fetch model info"}
        except Exception as e:
            logger.error(f"Error fetching model info: {e}")
            return {"error": str(e)}


# Provider selection
_provider = settings.AI_PROVIDER.lower() if settings.AI_PROVIDER else "ollama"
_service = None

if _provider == "tinyllama":
    try:
        from app.services.tinyllama_service import tinyllama_service
        _service = tinyllama_service
        logger.info("AI provider: TinyLlamaService (local llama_cpp)")
    except Exception as e:
        logger.warning(f"TinyLlamaService init failed, trying Ollama: {e}")

if _service is None:
    # Default to Ollama
    _service = AIService()
    logger.info(f"AI provider: AIService (Ollama at {settings.OLLAMA_BASE_URL})")

ai_service = _service


async def get_ai_service() -> object:
    """Dependency injection for the selected AI service."""
    return ai_service
