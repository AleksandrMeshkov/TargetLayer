import logging
import time
from typing import Optional, List, Dict

from app.core.settings.settings import settings
from app.schemas.ai_schemas import ChatMessage

logger = logging.getLogger(__name__)

try:
    from llama_cpp import Llama
    _HAS_LLAMA_CPP = True
except Exception:
    _HAS_LLAMA_CPP = False


class TinyLlamaService:
    """Adapter for running a tiny/llama-family model locally via `llama_cpp`.

    This class is optional and will raise a helpful error if `llama_cpp` is not
    installed. It preserves the same public methods used by the rest of the
    codebase so it can be used interchangeably with the Ollama-driven service.
    """

    def __init__(self):
        self.model_path = settings.TINYLLAMA_MODEL_PATH
        self.default_temperature = settings.AI_TEMPERATURE
        self.default_max_tokens = settings.AI_MAX_TOKENS
        self.n_ctx = settings.TINYLLAMA_N_CTX
        self.model = None

        if not _HAS_LLAMA_CPP:
            logger.warning("llama_cpp is not installed; TinyLlamaService will not work until installed.")
        else:
            if not self.model_path:
                logger.error("TINYLLAMA_MODEL_PATH is not set in settings; TinyLlamaService needs a model file path.")
            else:
                try:
                    self.model = Llama(model_path=self.model_path, n_ctx=self.n_ctx)
                except Exception as e:
                    logger.exception(f"Failed to initialize Llama model: {e}")
                    self.model = None

    async def check_model_availability(self) -> bool:
        return _HAS_LLAMA_CPP and self.model is not None

    async def chat(
        self,
        message: str,
        context: Optional[List[ChatMessage]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None,
    ) -> Dict:
        if not _HAS_LLAMA_CPP:
            return {"error": True, "message": "llama_cpp not installed"}
        if not self.model:
            return {"error": True, "message": "TinyLlama model not initialized; check TINYLLAMA_MODEL_PATH"}

        temperature = temperature if temperature is not None else self.default_temperature
        max_tokens = max_tokens if max_tokens is not None else min(1024, self.default_max_tokens)

        prompt = self._prepare_prompt(message, context or [], system_prompt)

        start_time = time.time()
        try:
            resp = self.model.create(
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            processing_time = time.time() - start_time

            text = ""
            if isinstance(resp, dict):
                choices = resp.get("choices") or []
                if choices:
                    text = choices[0].get("text", "")
                tokens_used = resp.get("usage", {}).get("total_tokens", 0)
            else:
                text = str(resp)
                tokens_used = 0

            return {
                "error": False,
                "response": text,
                "tokens_used": tokens_used,
                "processing_time": processing_time,
                "model": self.model_path,
                "cached": False,
            }

        except Exception as e:
            logger.exception(f"TinyLlama generation failed: {e}")
            return {"error": True, "message": str(e)}

    async def decompose_goal(self, goal: str, timeframe: Optional[str] = None, additional_info: Optional[str] = None) -> Dict:
        prompt = f"Разложи следующую цель на подцели и действия:\n\n"
        prompt += f"Цель: {goal}\n"
        if timeframe:
            prompt += f"Временные рамки: {timeframe}\n"
        if additional_info:
            prompt += f"Дополнительно: {additional_info}\n"
        prompt += "\nПредоставь структурированный ответ с подцелями, действиями и временной шкалой."
        return await self.chat(message=prompt, temperature=0.7, max_tokens=2048)

    async def generate_tasks(self, project_description: str, priority_level: str = "medium") -> Dict:
        prompt = f"Создай детальный список задач для следующего проекта:\n\n{project_description}\n"
        if priority_level:
            prompt += f"Уровень приоритета: {priority_level}\n"
        return await self.chat(message=prompt, temperature=0.6, max_tokens=2048)

    async def analyze(self, content: str, analysis_type: str = "general") -> Dict:
        prompt = f"Проанализируй следующее {analysis_type}:\n\n{content}"
        return await self.chat(message=prompt, temperature=0.5, max_tokens=2048)

    def _prepare_prompt(self, message: str, context: List[ChatMessage], system_prompt: Optional[str]) -> str:
        parts = []
        if system_prompt:
            parts.append(system_prompt)
        if context:
            for msg in context[-20:]:
                parts.append(f"{msg.role}: {msg.content}")
        parts.append(f"user: {message}")
        return "\n\n".join(parts)

    async def get_model_info(self) -> Dict:
        return {"model_path": self.model_path, "n_ctx": self.n_ctx, "available": await self.check_model_availability()}


tinyllama_service = TinyLlamaService()

async def get_tinyllama_service() -> TinyLlamaService:
    return tinyllama_service
