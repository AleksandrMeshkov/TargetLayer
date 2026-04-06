from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from yarl import URL
from typing import Optional
from pathlib import Path
from urllib.parse import urlencode

BASE_DIR = Path(__file__).resolve().parents[3]

class Settings(BaseSettings):
    POSTGRES_HOST: str
    POSTGRES_PORT: int
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    API_BASE_PORT: int 

    EMAIL_ADDRESS: str
    EMAIL_PASSWORD: str

    SECRET_KEY: str
    ALGORITHM: str 
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_HOURS: int
    RECOVERY_TOKEN_EXPIRE_HOURS: int = 1 
    INVITE_TOKEN_EXPIRE_HOURS: int = 24

    FRONTEND_URL: Optional[str] 
    FRONTEND_RESET_PASSWORD_PATH: str 
    FRONTEND_TEAM_INVITE_PATH: str = "/invite"
    CORS_ALLOW_ORIGINS: str
    SERVER_BASE_URL: str
    UPLOADS_DIR: str 
    UPLOADS_URL_PREFIX: str 
    
    ENVIRONMENT: str 

    PROXYAPI_KEY: Optional[str] 
    PROXYAPI_BASE_URL: str
    AI_MODEL: str 

    REFRESH_COOKIE_SAMESITE: Optional[str] = None
    REFRESH_COOKIE_SECURE: Optional[bool] = None
    REFRESH_COOKIE_DOMAIN: Optional[str] = None
    REFRESH_COOKIE_PATH: str = "/"

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    @property
    def db_url(self) -> str:  
        return str(URL.build(
            scheme="postgresql+asyncpg",
            host=self.POSTGRES_HOST,
            port=self.POSTGRES_PORT,
            user=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            path=f"/{self.POSTGRES_DB}"
        ))

    @property
    def cors_allow_origins(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ALLOW_ORIGINS.split(",") if origin.strip()]

    @property
    def uploads_dir_path(self) -> Path:
        uploads_path = Path(self.UPLOADS_DIR)
        if uploads_path.is_absolute():
            return uploads_path
        return BASE_DIR / uploads_path

    @property
    def avatars_dir_path(self) -> Path:
        return self.uploads_dir_path / "avatars"

    @property
    def server_base_url(self) -> str:
        return self.SERVER_BASE_URL.rstrip("/")

    @property
    def refresh_cookie_samesite(self) -> str:
        if self.REFRESH_COOKIE_SAMESITE:
            return self.REFRESH_COOKIE_SAMESITE.strip().lower()

        
        if (self.ENVIRONMENT or "").lower() == "production":
            return "lax"
        return "none" if self.server_base_url.lower().startswith("https://") else "lax"

    @property
    def refresh_cookie_secure(self) -> bool:
        if self.REFRESH_COOKIE_SECURE is not None:
            return bool(self.REFRESH_COOKIE_SECURE)

        if self.refresh_cookie_samesite == "none":
            return True
        return (self.ENVIRONMENT or "").lower() == "production"

    @property
    def refresh_cookie_domain(self) -> Optional[str]:
        if not self.REFRESH_COOKIE_DOMAIN:
            return None
        domain = self.REFRESH_COOKIE_DOMAIN.strip()
        return domain or None

    @property
    def refresh_cookie_path(self) -> str:
        path = (self.REFRESH_COOKIE_PATH or "/").strip()
        return path if path.startswith("/") else f"/{path}"

    def build_frontend_recovery_url(self, token: str) -> str:
        base = (self.FRONTEND_URL or self.server_base_url).rstrip("/")
        path = self.FRONTEND_RESET_PASSWORD_PATH.strip()
        if not path.startswith("/"):
            path = f"/{path}"
        query = urlencode({"token": token})
        return f"{base}{path}?{query}"

    def build_frontend_team_invite_url(self, token: str) -> str:
        base = (self.FRONTEND_URL or self.server_base_url).rstrip("/")
        path = (self.FRONTEND_TEAM_INVITE_PATH or "/invite").strip()
        if not path.startswith("/"):
            path = f"/{path}"
        query = urlencode({"token": token})
        return f"{base}{path}?{query}"

    def build_backend_team_invite_accept_url(self, token: str) -> str:
        base = self.server_base_url
        path = "/api/v1/teams/invite/accept"
        query = urlencode({"token": token})
        return f"{base}{path}?{query}"

settings = Settings()
