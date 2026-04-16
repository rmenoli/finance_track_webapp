import json
from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    api_v1_prefix: str = "/v1"
    project_name: str = "ETF Portfolio Tracker"
    debug: bool = False
    cors_origins: str = '["http://localhost:3000", "http://localhost:8000"]'
    api_key_db_map: str = ""  # JSON map of API key → database URL

    # ETF breakdown data
    etf_data_s3_bucket: str = ""
    etf_data_s3_prefix: str = "etf-data/"
    etf_data_dir: str = str(Path(__file__).resolve().parent.parent / "data")

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
