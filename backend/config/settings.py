"""ColdRescue configuration — reads from environment / .env file."""
from __future__ import annotations

from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application settings
    APP_ENV: str = "development"
    APP_DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    # AWS foundation — these settings do not create AWS resources.
    AWS_REGION: str = "ap-south-1"
    AWS_INTEGRATIONS_ENABLED: bool = False

    # CloudWatch Logs configuration.
    # These values do not enable AWS access or create resources.
    CLOUDWATCH_LOG_GROUP: str = "/coldrescue/application/development"
    CLOUDWATCH_LOG_STREAM: str = "local-development"

    # Amazon Location Service
    AWS_LOCATION_ROUTE_CALCULATOR_NAME: str = "ColdRescue-RouteCalculator-dev"

    # Application security
    SECRET_KEY: str = "dev-secret-key"

    @property
    def cors_origins_list(self) -> List[str]:
        return [
            origin.strip()
            for origin in self.CORS_ORIGINS.split(",")
            if origin.strip()
        ]


settings = Settings()