"""Redis core module - provides Redis client and dependency injection"""

from app.core.redis.redis import get_redis, redis_client

__all__ = ["get_redis", "redis_client"]
