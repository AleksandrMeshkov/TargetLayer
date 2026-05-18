import logging
import json
from typing import Any, Dict, Optional, List
import re

import httpx

from app.core.settings.settings import settings
from app.core.ai.ai_config import SYSTEM_PROMPT, GENERATION_CONFIG, MAX_RETRIES, RETRY_DELAY

logger = logging.getLogger(__name__)


class AIRoadmapService:

    def __init__(self):
        self.base_url = settings.PROXYAPI_BASE_URL.rstrip("/")
        self.api_key = settings.PROXYAPI_KEY
        self.model = settings.AI_MODEL
        self.timeout = 30

    async def chat(
        self, 
        user_message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        current_roadmap_context: Optional[Dict[str, Any]] = None,
        max_deadline_days: Optional[int] = None,
    ) -> Dict[str, Any]:
        
        if not self.api_key:
            raise ValueError("PROXYAPI_KEY not configured")

        url = self.base_url + "/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        system_prompt = SYSTEM_PROMPT
        if current_roadmap_context:
            system_prompt = self._build_system_prompt_with_context(SYSTEM_PROMPT, current_roadmap_context)

        if max_deadline_days is not None:
            system_prompt = self._build_system_prompt_with_deadline_limit(system_prompt, max_deadline_days)

        messages = [{"role": "system", "content": system_prompt}]
        if conversation_history:
            messages.extend(conversation_history)
        messages.append({"role": "user", "content": user_message})
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": GENERATION_CONFIG["temperature"],
            "max_tokens": GENERATION_CONFIG["max_tokens"],
        }

        for attempt in range(MAX_RETRIES):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    resp = await client.post(url, headers=headers, json=payload)
                resp.raise_for_status()

                response_data = resp.json()
                content = response_data.get("choices", [{}])[0].get("message", {}).get("content", "")

                if not content:
                    logger.error(f"Empty response from AI (attempt {attempt + 1})")
                    if attempt < MAX_RETRIES - 1:
                        await self._async_sleep(RETRY_DELAY)
                        continue
                    raise ValueError("Empty response from AI")

                parsed = self._parse_json_response(content)
                if max_deadline_days is not None:
                    parsed = self._normalize_deadlines(parsed, max_deadline_days)
                return parsed

            except httpx.HTTPStatusError as exc:
                logger.error(f"AI request failed: {exc.response.status_code} {exc.response.text}")
                raise
            except json.JSONDecodeError as exc:
                logger.error(f"Failed to parse AI response (attempt {attempt + 1}): {exc}")
                if attempt < MAX_RETRIES - 1:
                    await self._async_sleep(RETRY_DELAY)
                    continue
                raise ValueError("AI response is not valid JSON")
            except Exception as exc:
                logger.exception("Unexpected error in AI chat")
                raise

        raise ValueError("Max retries exceeded")

    @staticmethod
    def _build_system_prompt_with_context(
        base_prompt: str, 
        roadmap_context: Dict[str, Any]
    ) -> str:
        context_section = """

ТЕКУЩИЙ КОНТЕКСТ РОУДМАПА:
У пользователя уже есть роудмап в работе:
"""
        context_section += f"Название цели: {roadmap_context.get('goal_title', '')}\n"
        context_section += f"Описание цели: {roadmap_context.get('goal_description', '')}\n"
        context_section += f"Дата создания: {roadmap_context.get('created_at', '')}\n"
        
        if roadmap_context.get('tasks'):
            context_section += "\nТекущие задачи:\n"
            for idx, task in enumerate(roadmap_context['tasks'], 1):
                context_section += f"{idx}. {task.get('title', '')} - {task.get('description', '')}\n"
        
        context_section += """
ВАЖНО:
- Если пользователь просит изменить/переделать/отредактировать существующие задачи - РЕДАКТИРУЙ текущий роудмап
- Если пользователь просит добавить новые задачи - ДОБАВЛЯЙ их к существующему роудмапу
- Если пользователь просит полностью переделать роудмап - СОЗДАЙ НОВЫЙ роудмап
- Если пользователь не упоминает существующий роудмап и просит что-то новое - СОЗДАЙ НОВЫЙ роудмап

Когда редактируешь существующий роудмап - верни ВСЕ задачи (старые + отредактированные + новые) в одном ответе.
"""
        
        return base_prompt + context_section

    @staticmethod
    def _build_system_prompt_with_deadline_limit(base_prompt: str, max_deadline_days: int) -> str:
        return (
            f"{base_prompt}\n\n"
            f"ЛИМИТ СРОКА: пользователь указал срок {max_deadline_days} дней. "
            f"Ни одна задача не должна иметь deadline_offset_days больше {max_deadline_days}. "
            f"Последняя задача тоже обязана укладываться в этот срок."
        )

    @staticmethod
    def _normalize_deadlines(data: Dict[str, Any], max_deadline_days: int) -> Dict[str, Any]:
        tasks = data.get("tasks", [])
        if not isinstance(tasks, list):
            return data

        normalized_tasks = []
        for task in tasks:
            if not isinstance(task, dict):
                normalized_tasks.append(task)
                continue

            task_copy = dict(task)
            deadline = task_copy.get("deadline_offset_days")
            if isinstance(deadline, int):
                task_copy["deadline_offset_days"] = min(max(deadline, 0), max_deadline_days)
            normalized_tasks.append(task_copy)

        data = dict(data)
        data["tasks"] = normalized_tasks
        return data

    @staticmethod
    def _parse_json_response(content: str) -> Dict[str, Any]:
        cleaned = content.strip()

        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            cleaned = "\n".join(line for line in lines if not line.startswith("```"))
            cleaned = cleaned.strip()

        data = json.loads(cleaned)

        if not isinstance(data, dict):
            raise ValueError("Ожидаемый объект JSON на корневом уровне")
        if "goal_title" not in data or "tasks" not in data:
            raise ValueError("Отсутствуют необходимые поля: goal_title, tasks")
        if not isinstance(data["tasks"], list):
            raise ValueError("задачи должны представлять собой массив")

        return data

    @staticmethod
    async def _async_sleep(seconds: float):
        import asyncio
        await asyncio.sleep(seconds)


ai_service = AIRoadmapService()
