import logging
import json
from typing import Any, Dict, Optional

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

    async def chat(self, user_message: str) -> Dict[str, Any]:
        
        if not self.api_key:
            raise ValueError("PROXYAPI_KEY not configured")

        url = self.base_url + "/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
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
    def _parse_json_response(content: str) -> Dict[str, Any]:
        cleaned = content.strip()

        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            cleaned = "\n".join(line for line in lines if not line.startswith("```"))
            cleaned = cleaned.strip()

        data = json.loads(cleaned)

        if not isinstance(data, dict):
            raise ValueError("Expected JSON object at root level")
        if "goal_title" not in data or "tasks" not in data:
            raise ValueError("Missing required fields: goal_title, tasks")
        if not isinstance(data["tasks"], list):
            raise ValueError("tasks must be an array")

        return data

    @staticmethod
    async def _async_sleep(seconds: float):
        import asyncio
        await asyncio.sleep(seconds)


ai_service = AIRoadmapService()
