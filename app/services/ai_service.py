import httpx
import logging
from typing import Optional, Dict
import os
import asyncio
import time
import json
import re
import unicodedata

from app.core.ai.ai_config import SYSTEM_PROMPT, AI_TEMPERATURE, AI_MAX_TOKENS

logger = logging.getLogger(__name__)


class AIService:
    def __init__(self):
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.model_name = os.getenv("AI_MODEL_NAME", "phi3:mini")
        timeout_val = int(os.getenv("OLLAMA_TIMEOUT", "300"))
        self.timeout = httpx.Timeout(timeout=timeout_val)
        self._model_cache: Optional[bool] = None
        self._cache_time: float = 0.0

    async def check_model_availability(self) -> bool:
        """Проверка доступности модели (синхронный httpx в фоне + кэш 5s)"""
        now = time.time()
        if self._model_cache is not None and (now - self._cache_time) < 5:
            return self._model_cache

        def _check() -> bool:
            try:
                with httpx.Client(timeout=5.0) as client:
                    resp = client.get(f"{self.base_url}/api/tags")
                    if resp.status_code != 200:
                        return False
                    models = [m.get("name") for m in resp.json().get("models", [])]
                    return self.model_name in models
            except Exception as e:
                logger.debug(f"sync check error: {e}")
                return False

        result = await asyncio.to_thread(_check)
        self._model_cache = result
        self._cache_time = now
        if result:
            logger.info(f"✅ Модель {self.model_name} доступна")
        return result

    async def decompose_goal(self, goal: str, timeframe: Optional[str] = None) -> Dict:
        """Разложить цель на подцели и действия (синхронный httpx в фоне)."""
        # Ensure model present
        available = await self.check_model_availability()
        if not available:
            return {"error": True, "message": "Model unavailable", "model": self.model_name}

        prompt = f"Цель: {goal}\nСрок: {timeframe if timeframe else 'не указан'}\n\nВерни ТОЛЬКО валидный JSON согласно системе. Никакого другого текста."

        def _call() -> Dict:
            try:
                with httpx.Client(timeout=self.timeout) as client:
                    response = client.post(
                        f"{self.base_url}/api/chat",
                        json={
                            "model": self.model_name,
                            "messages": [
                                {"role": "system", "content": SYSTEM_PROMPT},
                                {"role": "user", "content": prompt},
                            ],
                            "temperature": AI_TEMPERATURE,
                            "stream": False,
                            "options": {"num_predict": AI_MAX_TOKENS},
                        },
                    )

                if response.status_code != 200:
                    logger.error(f"Ollama API error: {response.status_code}")
                    return {"error": True, "message": "Ollama error", "status_code": response.status_code}

                result = response.json()
                ai_text = result.get("message", {}).get("content", "")
                return {"error": False, "response": ai_text, "model": self.model_name}

            except Exception as e:
                logger.error(f"decompose_goal HTTP error: {str(e)}")
                return {"error": True, "message": str(e)}

        # Single call, skip JSON parsing for now — just return raw response
        result = await asyncio.to_thread(_call)
        return result


ai_service = AIService()


async def get_ai_service():
    return ai_service