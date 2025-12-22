from typing import Optional
import secrets
import httpx
from redis.asyncio import Redis
from app.core.settings.settings import settings

class EmailVerificationService:
    def __init__(self, redis: Redis):
        self.redis = redis
        self.supabase_url = settings.SUPABASE_URL.rstrip("/")
        self.service_key = settings.SUPABASE_SERVICE_ROLE_KEY
        self.timeout = 15.0
        self.code_ttl = 300

    async def is_verification_pending(self, email: str) -> bool:
        return await self.redis.exists(f"verify_code:{email}")

    async def get_remaining_ttl(self, email: str) -> int:
        ttl = await self.redis.ttl(f"verify_code:{email}")
        return ttl if ttl > 0 else 0

    async def send_verification_code(self, email: str) -> str:
        code = "".join(secrets.choice("0123456789") for _ in range(6))
        
        await self.redis.setex(f"verify_code:{email}", self.code_ttl, code)

        await self.send_verification_email(email)
        
        return code

    async def verify_code(self, email: str, code: str) -> bool:
        saved_code = await self.redis.get(f"verify_code:{email}")
        if saved_code and saved_code.decode('utf-8') == code:
            await self.redis.delete(f"verify_code:{email}")
            return True
        return False

    async def send_verification_email(self, email: str) -> None:
        temp_password = secrets.token_urlsafe(24)
        payload = {"email": email, "password": temp_password}
        url = f"{self.supabase_url}/auth/v1/signup"
        headers = {
            "apikey": self.service_key,
            "Authorization": f"Bearer {self.service_key}",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(url, json=payload, headers=headers)
            if resp.status_code not in (200, 201):
                raise Exception(f"Supabase signup failed: {resp.text}")