"""
Application configuration loaded from environment variables.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration sourced from .env file."""

    # App
    APP_ENV: str = "development"
    APP_SECRET_KEY: str = "change-me"

    # OpenAI
    OPENAI_API_KEY: str = ""

    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/lead_gen_tool"
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_MAX_CONNECTIONS: int = 10

    # AWS S3
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_S3_BUCKET_NAME: str = ""
    AWS_REGION: str = "us-east-1"

    # Celery Configuration
    CELERY_BROKER_URL: str = "redis://:redis123@localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://:redis123@localhost:6379/0"

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
