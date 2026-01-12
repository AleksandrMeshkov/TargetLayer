from typing import Any, Optional, Dict, Tuple
import time
import secrets
import httpx
from app.core.settings.settings import settings


class _LocalInMemoryStore:
	"""Minimal async-compatible in-memory store used when Redis is removed."""

	def __init__(self):
		self._store: Dict[str, Tuple[bytes, Optional[float]]] = {}

	async def exists(self, key: str) -> int:
		return 1 if key in self._store and not self._is_expired(key) else 0

	async def ttl(self, key: str) -> int:
		if key not in self._store or self._is_expired(key):
			return -2
		_, expire_at = self._store[key]
		if expire_at is None:
			return -1
		remaining = int(expire_at - time.time())
		return remaining if remaining > 0 else -2

	async def setex(self, key: str, ttl: int, value: str | bytes) -> bool:
		if isinstance(value, str):
			value = value.encode("utf-8")
		expire_at = time.time() + ttl if ttl and ttl > 0 else None
		self._store[key] = (value, expire_at)
		return True

	async def get(self, key: str) -> Optional[bytes]:
		if key not in self._store or self._is_expired(key):
			return None
		val, _ = self._store[key]
		return val

	async def delete(self, key: str) -> int:
		if key in self._store:
			del self._store[key]
			return 1
		return 0

	def _is_expired(self, key: str) -> bool:
		if key not in self._store:
			return True
		_, expire_at = self._store[key]
		if expire_at is None:
			return False
		if time.time() >= expire_at:
			del self._store[key]
			return True
		return False


class EmailVerificationService:
	def __init__(self, redis: Optional[Any] = None):
		# Use provided client or local in-memory store
		self.redis = redis if redis is not None else _LocalInMemoryStore()
		self.timeout = 15.0
		self.code_ttl = 300

	async def is_verification_pending(self, email: str) -> bool:
		return bool(await self.redis.exists(f"verify_code:{email}"))

	async def get_remaining_ttl(self, email: str) -> int:
		ttl = await self.redis.ttl(f"verify_code:{email}")
		return ttl if ttl and ttl > 0 else 0

	async def send_verification_code(self, email: str) -> str:
		code = "".join(secrets.choice("0123456789") for _ in range(6))

		await self.redis.setex(f"verify_code:{email}", self.code_ttl, code)

		# Email sending removed — return the generated code so caller can handle
		# delivery externally or for testing.
		return code

	async def verify_code(self, email: str, code: str) -> bool:
		saved_code = await self.redis.get(f"verify_code:{email}")
		if saved_code:
			if isinstance(saved_code, bytes):
				saved_code = saved_code.decode("utf-8")
			if saved_code == code:
				await self.redis.delete(f"verify_code:{email}")
				return True
		return False

	# Email sending and Supabase signup removed from this service.
