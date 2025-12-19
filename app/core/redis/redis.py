import redis.asyncio as redis
from app.core.settings.settings import settings

# Создание Redis клиента с использованием URL из settings
redis_client = redis.from_url(
    settings.redis_url,
    encoding="utf-8", 
    decode_responses=True
)

async def get_redis():
    """Возвращает Redis клиент для dependency injection"""
    return redis_client