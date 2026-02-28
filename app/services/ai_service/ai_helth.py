import logging
from typing import Any, Dict

import httpx

from app.core.settings.settings import settings

logger = logging.getLogger(__name__)


async def check_ai_health() -> Dict[str, Any]:
    
    if not settings.PROXYAPI_KEY:
        return {"ok": False, "error": "PROXYAPI_KEY not set"}

    url = settings.PROXYAPI_BASE_URL.rstrip("/") + "/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.PROXYAPI_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": settings.AI_MODEL,
        "messages": [{"role": "system", "content": "health check"}],
        "max_tokens": 1,
    }

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(url, headers=headers, json=payload)
        resp.raise_for_status()
        return {"ok": True, "status": "ready"}
    except httpx.HTTPStatusError as exc:
        logger.error("AI health check failed HTTP: %s %s",
                     exc.response.status_code, exc.response.text)
        return {"ok": False, "error": f"{exc.response.status_code} {exc.response.text}"}
    except Exception as exc:
        logger.exception("AI health check exception")
        return {"ok": False, "error": str(exc)}
