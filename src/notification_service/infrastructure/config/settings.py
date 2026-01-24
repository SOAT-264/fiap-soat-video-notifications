"""Application Settings."""
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SERVICE_NAME: str = "notification-service"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5435/notification_db"
    REDIS_URL: str = "redis://localhost:6379/3"

    # SMTP Configuration
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "noreply@video-processor.com"
    SMTP_USE_TLS: bool = True

    AUTH_SERVICE_URL: str = "http://localhost:8001"
    JOB_SERVICE_URL: str = "http://localhost:8003"

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
