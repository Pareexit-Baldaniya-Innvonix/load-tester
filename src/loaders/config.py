from typing import Set
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # ENV config
    ENV: str = Field(..., env="ENV")

    # App config
    APP_NAME: str = Field(..., env="APP_NAME")
    APP_HOST: str = Field(..., env="APP_HOST")
    APP_PORT: int = Field(..., env="APP_PORT")
    ALLOWED_HOSTS: str = Field(..., env="ALLOWED_HOSTS")
    API_URL: str = Field(..., env="API_URL")

    # Log config
    LOG_LEVEL: str = Field(..., env="LOG_LEVEL")

    # Database credentials
    DATABASE_URL: str = Field(..., env="DATABASE_URL")


config = Settings()
