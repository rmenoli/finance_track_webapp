import json
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    database_url: str
    api_v1_prefix: str = "/v1"
    project_name: str = "ETF Portfolio Tracker"
    debug: bool = False
    cors_origins: str = '["http://localhost:3000", "http://localhost:8000"]'
    s3_bucket_backups: str = "etf-portfolio-backups-20251225"
    s3_bucket_db: str = "etf-porfolio-backend-live-20260317"
    s3_db_key: str = "portfolio.db"
    use_s3: bool = True

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


settings = Settings()
