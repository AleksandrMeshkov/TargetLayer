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

    EMAIL_ADDRESS: str
    EMAIL_PASSWORD: str

    SECRET_KEY: str
    ALGORITHM: str 
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_HOURS: int
    RECOVERY_TOKEN_EXPIRE_HOURS: int = 1 

    FRONTEND_URL: Optional[str] = None

    AI_PROVIDER: str = "ollama"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_TIMEOUT: int = 300

    
    PROXYAPI_KEY: Optional[str] = None
    PROXYAPI_BASE_URL: str = "https://api.proxyapi.ru/openai/v1"
    AI_MODEL: str = "gpt-4o"

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

settings = Settings()
