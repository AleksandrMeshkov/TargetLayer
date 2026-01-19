import httpx
import json
import logging
import asyncio
from typing import Optional, Dict, Any

from app.core.ai.ai_config import (
    SYSTEM_PROMPT, OLLAMA_BASE_URL, OLLAMA_TIMEOUT, 
    AI_MODEL_NAME, GENERATION_CONFIG, MAX_RETRIES, RETRY_DELAY
)

logger = logging.getLogger(__name__)


class AIServiceError(Exception):
    pass


class AIService:
    
    def __init__(self):
        self.base_url = OLLAMA_BASE_URL
        self.model_name = AI_MODEL_NAME
        self.timeout = OLLAMA_TIMEOUT
        self.max_retries = MAX_RETRIES
        self.retry_delay = RETRY_DELAY
        self.client = httpx.AsyncClient(timeout=self.timeout)
        logger.info(f"AIService инициализирован: модель={self.model_name}, url={self.base_url}")

    async def check_model_availability(self) -> bool:
       
        try:
            response = await self.client.get(
                f"{self.base_url}/api/tags",
                timeout=5.0
            )
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [m.get("name") for m in models]
                is_available = self.model_name in model_names
                logger.debug(f"Модель {self.model_name} доступна: {is_available}")
                return is_available
            else:
                logger.warning(f"Ollama вернул статус {response.status_code}")
                return False
        except httpx.TimeoutException:
            logger.error("Таймаут при проверке доступности модели")
            return False
        except Exception as e:
            logger.error(f"Ошибка проверки модели: {e}", exc_info=True)
            return False

    def _extract_json_from_text(self, text: str) -> str:
       
        if "```json" in text:
            return text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            return text.split("```")[1].split("```")[0].strip()
        return text.strip()

    async def decompose_goal(self, goal: str, timeframe: Optional[str] = None) -> Dict[str, Any]:
        
        prompt = f"Цель: {goal}"
        if timeframe:
            prompt += f"\nСрок: {timeframe}"
        
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            "stream": False,
            "options": GENERATION_CONFIG,
        }
        
        for attempt in range(self.max_retries):
            try:
                logger.debug(f"Попытка {attempt + 1}/{self.max_retries} разложить цель")
                
                response = await self.client.post(
                    f"{self.base_url}/api/chat",
                    json=payload,
                    timeout=self.timeout
                )
                
                if response.status_code != 200:
                    if attempt < self.max_retries - 1:
                        logger.warning(f"Статус {response.status_code}, повтор через {self.retry_delay}с")
                        await asyncio.sleep(self.retry_delay)
                        continue
                    return {
                        "error": True, 
                        "message": f"AI вернул статус {response.status_code}",
                        "tokens_used": None,
                        "processing_time": None
                    }
                
                result = response.json()
                ai_text = result.get("message", {}).get("content", "").strip()
                
                tokens_used = result.get("eval_count", None)  
                total_duration = result.get("total_duration", 0) 
                processing_time = total_duration / 1e9 if total_duration else None  
                
                if not ai_text:
                    return {
                        "error": True, 
                        "message": "Пустой ответ от AI",
                        "tokens_used": tokens_used,
                        "processing_time": processing_time
                    }
                
                try:
                    cleaned_text = self._extract_json_from_text(ai_text)
                    parsed_json = json.loads(cleaned_text)
                    
                    logger.info(f"Цель успешно разложена на этапы ({tokens_used} токенов, {processing_time:.2f}с)")
                    return {
                        "error": False,
                        "response": json.dumps(parsed_json, ensure_ascii=False),
                        "json": parsed_json,
                        "model": self.model_name,
                        "tokens_used": tokens_used,
                        "processing_time": processing_time,
                    }
                    
                except json.JSONDecodeError as je:
                    logger.warning(f"Ошибка парсинга JSON: {je}, ответ: {ai_text[:100]}")
                    return {
                        "error": False,
                        "response": ai_text,
                        "json": None,
                        "model": self.model_name,
                        "tokens_used": tokens_used,
                        "processing_time": processing_time,
                    }
                    
            except httpx.TimeoutException:
                if attempt < self.max_retries - 1:
                    logger.warning(f"Таймаут, повтор через {self.retry_delay}с")
                    await asyncio.sleep(self.retry_delay)
                    continue
                return {
                    "error": True, 
                    "message": "Таймаут запроса к AI",
                    "tokens_used": None,
                    "processing_time": None
                }
            except Exception as e:
                if attempt < self.max_retries - 1:
                    logger.warning(f"Ошибка: {e}, повтор через {self.retry_delay}с")
                    await asyncio.sleep(self.retry_delay)
                    continue
                logger.error(f"Ошибка AIService после {self.max_retries} попыток: {e}", exc_info=True)
                return {
                    "error": True, 
                    "message": str(e),
                    "tokens_used": None,
                    "processing_time": None
                }
        
        return {
            "error": True, 
            "message": "Все попытки исчерпаны",
            "tokens_used": None,
            "processing_time": None
        }

    async def close(self) -> None:
        await self.client.aclose()
        logger.info("AIService закрыт")


_ai_service: Optional[AIService] = None


def get_ai_service_instance() -> AIService:
    global _ai_service
    if _ai_service is None:
        _ai_service = AIService()
    return _ai_service


async def get_ai_service() -> AIService:
    return get_ai_service_instance()


async def close_ai_service() -> None:
    global _ai_service
    if _ai_service is not None:
        await _ai_service.close()
        _ai_service = None