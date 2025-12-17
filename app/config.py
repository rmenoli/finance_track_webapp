import json
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    database_url: str
    api_v1_prefix: str = "/api/v1"
    project_name: str = "ETF Portfolio Tracker"
    debug: bool = False
    cors_origins: str = '["http://localhost:3000", "http://localhost:8000"]'

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from JSON string to list."""
        return json.loads(self.cors_origins)


settings = Settings()
