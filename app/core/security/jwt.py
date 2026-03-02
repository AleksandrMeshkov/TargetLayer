from datetime import datetime, timedelta, timezone
from typing import Any
from jwt import encode, decode, ExpiredSignatureError, InvalidTokenError
from app.core.settings.settings import settings


class JWTManager:

    def __init__(self):
        self.secret_key = settings.SECRET_KEY
        self.algorithm = settings.ALGORITHM
        self.access_expire = settings.ACCESS_TOKEN_EXPIRE_MINUTES
        self.refresh_expire = settings.REFRESH_TOKEN_EXPIRE_HOURS
        self.recovery_expire = getattr(settings, "RECOVERY_TOKEN_EXPIRE_HOURS", 1)

    def _create_token(
        self, subject: str, expires_delta: timedelta, token_type: str
    ) -> str:
        expire = datetime.now(timezone.utc) + expires_delta
        payload: dict[str, Any] = {"sub": subject, "exp": expire, "type": token_type}
        return encode(payload, self.secret_key, algorithm=self.algorithm)

    def create_access_token(self, subject: str) -> str:
        return self._create_token(
            subject, timedelta(minutes=self.access_expire), "access"
        )

    def create_refresh_token(self, subject: str) -> str:
        return self._create_token(
            subject, timedelta(hours=self.refresh_expire), "refresh"
        )

    def create_recovery_token(self, subject: str) -> str:
        return self._create_token(
            subject, timedelta(hours=self.recovery_expire), "recovery"
        )

    def _decode(self, token: str) -> dict[str, Any]:
        try:
            return decode(token, self.secret_key, algorithms=[self.algorithm])
        except ExpiredSignatureError:
            raise
        except InvalidTokenError:
            raise

    def verify_access_token(self, token: str) -> str:
        payload = self._decode(token)
        if payload.get("type") != "access":
            raise InvalidTokenError("wrong token type")
        return payload.get("sub")

    def verify_refresh_token(self, token: str) -> str:
        payload = self._decode(token)
        if payload.get("type") != "refresh":
            raise InvalidTokenError("wrong token type")
        return payload.get("sub")

    def verify_recovery_token(self, token: str) -> str:
        payload = self._decode(token)
        if payload.get("type") != "recovery":
            raise InvalidTokenError("wrong token type")
        return payload.get("sub")

    def rotate_tokens(self, refresh_token: str) -> tuple[str, str]:
        subject = self.verify_refresh_token(refresh_token)
        return self.create_access_token(subject), self.create_refresh_token(subject)
