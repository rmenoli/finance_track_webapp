import json
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    database_url: str = ""
    api_v1_prefix: str = "/v1"
    project_name: str = "ETF Portfolio Tracker"
    debug: bool = False
    cors_origins: str = '["http://localhost:3000", "http://localhost:8000"]'
    api_key_db_map: str = ""  # JSON map of API key → database URL

    # Logging configuration
    log_level: str = "INFO"
    log_format: str = "json"  # json or text

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False
    )

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from JSON string to list."""
        return json.loads(self.cors_origins)

    @property
    def api_key_db_map_parsed(self) -> dict[str, str]:
        """Parse API_KEY_DB_MAP from JSON string to dict."""
        if not self.api_key_db_map:
            return {}
        return json.loads(self.api_key_db_map)


settings = Settings()
