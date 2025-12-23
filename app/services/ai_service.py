import httpx
import logging
import time
import hashlib
from typing import Optional, List, Dict
from datetime import datetime

from app.core.settings.settings import settings
from app.core.ai.ai_config import (
    SYSTEM_PROMPT_CHAT,
    SYSTEM_PROMPT_GOAL_DECOMPOSITION,
    SYSTEM_PROMPT_TASK_GENERATION,
    SYSTEM_PROMPT_ANALYSIS,
    SYSTEM_PROMPT_ROADMAP,
    OLLAMA_CONNECTION_TIMEOUT,
    ERRORS,
)
from app.schemas.ai_schemas import ChatMessage
from app.core.ai.ai_helpers import response_cache

logger = logging.getLogger(__name__)


class AIService:

    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL
        self._model_name = settings.AI_MODEL_NAME
        self.default_temperature = settings.AI_TEMPERATURE
        self.default_max_tokens = settings.AI_MAX_TOKENS

        timeout_value = settings.OLLAMA_TIMEOUT
        self.timeout = httpx.Timeout(
            timeout=timeout_value,
            connect=OLLAMA_CONNECTION_TIMEOUT,
            read=timeout_value,
        )

    @property
    def model_name(self) -> str:
        return self._model_name

    async def check_model_availability(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                if response.status_code == 200:
                    data = response.json()
                    models = [m.get("name") for m in data.get("models", [])]
                    is_available = self._model_name in models
                    if not is_available:
                        logger.warning(f"Модель {self._model_name} не найдена. Доступны: {models}")
                    return is_available
                return False
        except Exception as e:
            logger.error(f"Ошибка проверки доступности модели: {e}")
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
            temp = temperature if temperature is not None else self.default_temperature
            tokens = max_tokens if max_tokens is not None else self.default_max_tokens
            sys_prompt = system_prompt or SYSTEM_PROMPT_CHAT

            cache_data = f"{message}_{sys_prompt}_{temp}_{tokens}"
            cache_key = hashlib.md5(cache_data.encode()).hexdigest()

            cached_res = response_cache.get(cache_key)
            if cached_res:
                logger.info("Ответ взят из кэша")
                cached_res["cached"] = True
                return cached_res

            messages = self._prepare_messages(message, context, sys_prompt)
            start_time = time.time()

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json={
                        "model": self._model_name,
                        "messages": messages,
                        "temperature": temp,
                        "stream": False,
                        "options": {"num_predict": tokens},
                    },
                )

            processing_time = time.time() - start_time

            if response.status_code != 200:
                logger.error(f"Ошибка AI API: {response.status_code}")
                return {
                    "error": True,
                    "message": ERRORS.get("SERVER_ERROR", "Ошибка сервера"),
                    "status_code": response.status_code,
                }

            result = response.json()
            ai_response_text = result.get("message", {}).get("content", "")

            output = {
                "error": False,
                "response": ai_response_text,
                "tokens_used": result.get("eval_count", 0),
                "processing_time": round(processing_time, 2),
                "model": self._model_name,
                "cached": False,
                "timestamp": datetime.now().isoformat()
            }

            response_cache.set(cache_key, output)

            return output

        except httpx.TimeoutException:
            return {"error": True, "message": ERRORS.get("TIMEOUT")}
        except httpx.ConnectError:
            return {"error": True, "message": ERRORS.get("CONNECTION_ERROR")}
        except Exception as e:
            logger.error(f"Непредвиденная ошибка AIService: {e}")
            return {"error": True, "message": str(e)}

    async def decompose_goal(self, goal: str, timeframe: Optional[str] = None, additional_info: Optional[str] = None) -> Dict:
        prompt = f"Цель: {goal}. Таймфрейм: {timeframe if timeframe else 'не указан'}. {additional_info or ''}"
        return await self.chat(
            message=prompt,
            temperature=0.5,
            max_tokens=2048,
            system_prompt=SYSTEM_PROMPT_GOAL_DECOMPOSITION
        )

    async def generate_tasks(self, project_description: str, priority_level: str = "medium") -> Dict:
        return await self.chat(
            message=project_description,
            temperature=0.6,
            max_tokens=2048,
            system_prompt=SYSTEM_PROMPT_TASK_GENERATION
        )

    async def analyze(self, content: str, analysis_type: str = "general") -> Dict:
        return await self.chat(
            message=content,
            temperature=0.3,
            max_tokens=2048,
            system_prompt=SYSTEM_PROMPT_ANALYSIS
        )

    async def generate_roadmap(self, goal: str, timeframe: str, current_level: Optional[str] = None, available_time: Optional[str] = None, preferences: Optional[List[str]] = None) -> Dict:
        try:
            prompt_parts = [f"ЦЕЛЬ: {goal}", f"СРОК: {timeframe}"]
            if current_level:
                prompt_parts.append(f"ТЕКУЩИЙ УРОВЕНЬ: {current_level}")
            if available_time:
                prompt_parts.append(f"ДОСТУПНОЕ ВРЕМЯ: {available_time}")
            if preferences:
                prompt_parts.append(f"ПРЕДПОЧТЕНИЯ: {', '.join(preferences)}")
            prompt_parts.append("\nПожалуйста, создай детальный пошаговый роадмап с четкими задачами.")
            full_prompt = "\n".join(prompt_parts)

            result = await self.chat(
                message=full_prompt,
                temperature=0.3,
                max_tokens=3000,
                system_prompt=SYSTEM_PROMPT_ROADMAP
            )

            if result.get("error"):
                return result

            roadmap_text = result["response"]
            tasks = self._extract_tasks_from_roadmap(roadmap_text)

            return {
                "error": False,
                "roadmap": roadmap_text,
                "tasks": tasks,
                "structured_tasks": self._structure_tasks_for_db(tasks),
                "tokens_used": result.get("tokens_used"),
                "processing_time": result.get("processing_time"),
                "model": self._model_name
            }

        except Exception as e:
            logger.error(f"Ошибка генерации роадмапа: {e}")
            return {"error": True, "message": str(e)}

    def _extract_tasks_from_roadmap(self, roadmap_text: str) -> List[Dict]:
        tasks = []
        lines = roadmap_text.split('\n')

        current_month = None
        current_stage = None

        for line in lines:
            line = line.strip()

            if line.startswith('### МЕСЯЦ'):
                parts = line.split(':')
                if len(parts) > 1:
                    current_month = parts[0].replace('### МЕСЯЦ', '').strip()
                    current_stage = parts[1].strip()

            elif line and any(marker in line for marker in ['1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.']):
                task = {
                    'month': current_month,
                    'stage': current_stage,
                    'task': line,
                    'completed': False,
                    'metrics': self._extract_metrics(line),
                    'deadline': self._extract_deadline(line)
                }
                tasks.append(task)

        return tasks

    def _extract_metrics(self, task_text: str) -> str:
        if '**Метрика:**' in task_text:
            parts = task_text.split('**Метрика:**')
            if len(parts) > 1:
                return parts[1].split('-')[0].strip()
        return ""

    def _extract_deadline(self, task_text: str) -> str:
        if '**Срок:**' in task_text:
            parts = task_text.split('**Срок:**')
            if len(parts) > 1:
                return parts[1].split('-')[0].strip()
        return ""

    def _structure_tasks_for_db(self, tasks: List[Dict]) -> List[Dict]:
        structured = []
        for task in tasks:
            structured.append({
                'title': task['task'].split('. ')[1] if '. ' in task['task'] else task['task'],
                'description': task['task'],
                'month': task['month'],
                'stage': task['stage'],
                'metrics': task['metrics'],
                'deadline': task['deadline'],
                'priority': self._determine_priority(task['month']),
                'estimated_time': '1 неделя',
                'dependencies': []
            })
        return structured

    def _determine_priority(self, month_str: str) -> str:
        try:
            month_num = int(''.join(filter(str.isdigit, month_str)))
            if month_num <= 1:
                return "high"
            elif month_num <= 3:
                return "medium"
            else:
                return "low"
        except:
            return "medium"

    def _prepare_messages(self, message: str, context: Optional[List[ChatMessage]], system_prompt: str) -> List[Dict]:
        messages = [{"role": "system", "content": system_prompt}]
        if context:
            for msg in context[-10:]:
                messages.append({"role": msg.role, "content": msg.content})
        messages.append({"role": "user", "content": message})
        return messages


ai_service = AIService()


async def get_ai_service():
    return ai_service