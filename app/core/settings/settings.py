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

    FRONTEND_URL: Optional[str] 
    FRONTEND_RESET_PASSWORD_PATH: str 
    CORS_ALLOW_ORIGINS: str
    SERVER_BASE_URL: str
    UPLOADS_DIR: str 
    UPLOADS_URL_PREFIX: str 
    
    ENVIRONMENT: str 

    PROXYAPI_KEY: Optional[str] 
    PROXYAPI_BASE_URL: str
    AI_MODEL: str 

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

    def build_frontend_recovery_url(self, token: str) -> str:
        base = (self.FRONTEND_URL or self.server_base_url).rstrip("/")
        path = self.FRONTEND_RESET_PASSWORD_PATH.strip()
        if not path.startswith("/"):
            path = f"/{path}"
        query = urlencode({"token": token})
        return f"{base}{path}?{query}"

settings = Settings()
