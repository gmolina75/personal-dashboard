"""Application configuration using pydantic-settings.

Provides environment variable based settings with defaults suitable for development.
"""

import os
import logging
from pydantic_settings import BaseSettings, SettingsConfigDict

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='{"time": "%(asctime)s", "level": "%(levelname)s", "name": "%(name)s", "message": "%(message)s"}',
)
logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    google_client_id: str = ""
    google_client_secret: str = ""
    minimax_api_key: str = ""
    database_url: str = "sqlite+aiosqlite:///./data/dashboard.db"
    
    # CORS origins (comma-separated in env)
    cors_origins: str = "http://localhost:8000,http://127.0.0.1:8000"
    
    # Sync configuration
    sync_interval_minutes: int = 15
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )
    
    @property
    def cors_origins_list(self) -> list[str]:
        """Get CORS origins as a list."""
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


# Instantiate a singleton settings object used throughout the app.
settings = Settings()

logger.info(f"Configuration loaded: database={settings.database_url}, sync_interval={settings.sync_interval_minutes}min")
