import httpx
import json
import logging
from typing import Optional, Dict

from app.core.ai.ai_config import SYSTEM_PROMPT, OLLAMA_BASE_URL, OLLAMA_TIMEOUT, AI_MODEL_NAME, GENERATION_CONFIG

logger = logging.getLogger(__name__)


class AIService:
    def __init__(self):
        self.base_url = OLLAMA_BASE_URL
        self.model_name = AI_MODEL_NAME
        self.timeout = OLLAMA_TIMEOUT
        self.client = httpx.AsyncClient(timeout=self.timeout)

    async def check_model_availability(self) -> bool:
        """Проверить доступность модели"""
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [m.get("name") for m in models]
                return self.model_name in model_names
        except Exception as e:
            logger.error(f"Ошибка проверки модели: {e}")
        return False

    async def decompose_goal(self, goal: str, timeframe: Optional[str] = None) -> Dict:
        """Разложить цель на этапы"""
        
        # Формируем промпт
        prompt = f"Цель: {goal}"
        if timeframe:
            prompt += f"\nСрок: {timeframe}"
        
        try:
            # Отправляем запрос к Ollama
            response = await self.client.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model_name,
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": prompt}
                    ],
                    "stream": False,
                    "options": GENERATION_CONFIG,
                }
            )
            
            if response.status_code != 200:
                return {"error": True, "message": "Ошибка AI сервиса"}
            
            # Получаем ответ
            result = response.json()
            ai_text = result.get("message", {}).get("content", "").strip()
            
            # Пытаемся распарсить JSON
            try:
                # Очищаем ответ от лишних символов
                if "```json" in ai_text:
                    ai_text = ai_text.split("```json")[1].split("```")[0].strip()
                elif "```" in ai_text:
                    ai_text = ai_text.split("```")[1].split("```")[0].strip()
                
                parsed_json = json.loads(ai_text)
                
                return {
                    "error": False,
                    "response": json.dumps(parsed_json, ensure_ascii=False),
                    "json": parsed_json,
                    "model": self.model_name,
                }
                
            except json.JSONDecodeError:
                # Если не JSON, возвращаем как текст
                return {
                    "error": False,
                    "response": ai_text,
                    "json": None,
                    "model": self.model_name,
                }
                
        except httpx.TimeoutException:
            return {"error": True, "message": "Таймаут запроса к AI"}
        except Exception as e:
            logger.error(f"Ошибка AIService: {e}")
            return {"error": True, "message": str(e)}

    async def close(self):
        """Закрыть клиент"""
        await self.client.aclose()


# Создаем экземпляр сервиса
ai_service = AIService()


async def get_ai_service():
    return ai_service


async def close_ai_service():
    await ai_service.close()