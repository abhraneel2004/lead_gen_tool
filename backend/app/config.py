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

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # AWS S3
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_S3_BUCKET_NAME: str = ""
    AWS_REGION: str = "us-east-1"

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
