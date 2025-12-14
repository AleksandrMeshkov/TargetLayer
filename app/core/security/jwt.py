from datetime import datetime, timedelta, timezone
from typing import Union
from jwt import encode, decode, ExpiredSignatureError, InvalidTokenError
from app.core.settings.settings import settings

class JWTManager:

    def __init__(self):
        self.secret_key = settings.SECRET_KEY
        self.algorithm = settings.ALGORITHM
        self.access_expire = settings.ACCESS_TOKEN_EXPIRE_MINUTES
        self.refresh_expire = settings.REFRESH_TOKEN_EXPIRE_HOURS

    def create_access_token(self, subject: str) -> str:
        expire = datetime.now(timezone.utc) + timedelta(minutes=self.access_expire)
        payload = {"sub": subject, "exp": expire, "type": "access"}
        return encode(payload, self.secret_key, algorithm=self.algorithm)

    def create_refresh_token(self, subject: str) -> str:
        expire = datetime.now(timezone.utc) + timedelta(hours=self.refresh_expire)
        payload = {"sub": subject, "exp": expire, "type": "refresh"}
        return encode(payload, self.secret_key, algorithm=self.algorithm)

    def decode_token(self, token: str) -> Union[dict, str]:
        try:
            payload = decode(token, self.secret_key, algorithms=[self.algorithm])
            if payload.get("type") not in ("access", "refresh"):
                return "Invalid token type"
            return payload
        except ExpiredSignatureError:
            return "Token expired"
        except InvalidTokenError:
            return "Invalid token"
        except Exception:
            return "Invalid token structure"