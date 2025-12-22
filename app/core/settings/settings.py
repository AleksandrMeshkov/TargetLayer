from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from yarl import URL
from typing import Optional

class Settings(BaseSettings):
    POSTGRES_HOST: str
    POSTGRES_PORT: int
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    API_BASE_PORT: int 

    SECRET_KEY: str
    ALGORITHM: str 
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_HOURS: int 

    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None


    SUPABASE_URL: Optional[str] = None
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = None
    SUPABASE_ANON_KEY: Optional[str] = None

    AI_PROVIDER: str = "ollama"

    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_TIMEOUT: int = 120
    AI_MODEL_NAME: str = "tinyllama"

    TINYLLAMA_MODEL_PATH: Optional[str] = None
    TINYLLAMA_N_CTX: int = 2048

    AI_MAX_TOKENS: int = 4096
    AI_TEMPERATURE: float = 0.7
    AI_CACHE_TTL: int = 3600
    AI_ENABLED: bool = True

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
    def redis_url(self) -> str:
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

settings = Settings()