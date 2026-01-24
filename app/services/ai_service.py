import httpx
import logging
import asyncio
from typing import Optional
from datetime import datetime

from app.core.ai.ai_config import (
    SYSTEM_PROMPT, OLLAMA_BASE_URL, OLLAMA_TIMEOUT,
    AI_MODEL_NAME, GENERATION_CONFIG, MAX_RETRIES, RETRY_DELAY
)
from app.schemas.ai_schemas import AIResponse, GoalDecompositionRequest
from app.services.json_parser import JSONParser

logger = logging.getLogger(__name__)


class AIService:
    
    def __init__(self):
        self.base_url = OLLAMA_BASE_URL
        self.model_name = AI_MODEL_NAME
        self.timeout = OLLAMA_TIMEOUT
        self.max_retries = MAX_RETRIES
        self.retry_delay = RETRY_DELAY
        self.client = httpx.AsyncClient(timeout=self.timeout)
        self.parser = JSONParser()
        logger.info(f"AIService: {self.model_name}")
    
    async def check_health(self) -> bool:
        try:
            response = await self.client.get(f"{self.base_url}/api/tags", timeout=5.0)
            if response.status_code == 200:
                models = response.json().get("models", [])
                return any(m.get("name") == self.model_name for m in models)
            return False
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
    
    async def decompose_goal(self, request: GoalDecompositionRequest) -> dict:
        start_time = datetime.now()
        
        prompt = f"""Цель: {request.goal}
Срок: {request.timeframe_months} месяцев
{f'Уровень: {request.current_level}' if request.current_level else ''}
Часов в неделю: {request.weekly_hours}
"""
        
        for attempt in range(self.max_retries):
            try:
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
                    },
                    timeout=self.timeout
                )
                
                if response.status_code != 200:
                    logger.warning(f"AI returned {response.status_code}")
                    await asyncio.sleep(self.retry_delay)
                    continue
                
                result = response.json()
                ai_text = result.get("message", {}).get("content", "").strip()
                tokens = result.get("eval_count")
                
                if not ai_text:
                    raise ValueError("Empty response from AI")
                
                try:
                    parsed = self.parser.parse(ai_text)
                    
                    parsed = self._correct_response(parsed, request.timeframe_months)
                    
                    ai_response = AIResponse(**parsed)
                    
                    processing_time = (datetime.now() - start_time).total_seconds()
                    logger.info(f"Goal decomposed: {len(ai_response.tasks)} tasks")
                    
                    return {
                        "success": True,
                        "data": ai_response,
                        "tokens": tokens,
                        "time": processing_time,
                        "model": self.model_name
                    }
                except Exception as e:
                    logger.error(f"Validation error: {e}")
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(self.retry_delay)
                        continue
                    
                    return {
                        "success": False,
                        "error": str(e),
                        "time": (datetime.now() - start_time).total_seconds()
                    }
                    
            except httpx.TimeoutException:
                logger.warning("Timeout")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
                    continue
                    
                return {
                    "success": False,
                    "error": "Timeout",
                    "time": (datetime.now() - start_time).total_seconds()
                }
            except Exception as e:
                logger.error(f"Error: {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
                    continue
                    
                return {
                    "success": False,
                    "error": str(e),
                    "time": (datetime.now() - start_time).total_seconds()
                }
        
        return {
            "success": False,
            "error": "All retries exhausted",
            "time": (datetime.now() - start_time).total_seconds()
        }
    
    def _correct_response(self, data: dict, timeframe_months: int) -> dict:
        max_days = timeframe_months * 30
        
        if "tasks" in data:
            for task in data["tasks"]:
                if "estimated_duration_days" in task:
                    if task["estimated_duration_days"] <= 0:
                        task["estimated_duration_days"] = max(1, max_days // max(len(data["tasks"]), 1))
                    task["estimated_duration_days"] = min(task["estimated_duration_days"], max_days)
                
                if "deadline_offset_days" in task:
                    if task["deadline_offset_days"] < 0:
                        task["deadline_offset_days"] = max(1, 30)
                    task["deadline_offset_days"] = min(task["deadline_offset_days"], max_days)
                
                if "priority" not in task or task["priority"] not in ["high", "medium", "low"]:
                    task["priority"] = "medium"
                
                if "resources" not in task:
                    task["resources"] = []
                elif not isinstance(task["resources"], list):
                    task["resources"] = []
        
        return data
    
    async def close(self):
        await self.client.aclose()


_ai_service: Optional[AIService] = None


async def get_ai_service() -> AIService:
    global _ai_service
    if _ai_service is None:
        _ai_service = AIService()
    return _ai_service


async def close_ai_service():
    global _ai_service
    if _ai_service:
        await _ai_service.close()
        _ai_service = None
