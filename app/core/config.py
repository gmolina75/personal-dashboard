"""Application configuration using pydantic-settings.

Provides environment variable based settings with defaults suitable for development.
"""

import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    google_client_id: str = ""
    google_client_secret: str = ""
    minimax_api_key: str = ""
    database_url: str = "sqlite+aiosqlite:///./data/dashboard.db"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

# Instantiate a singleton settings object used throughout the app.
settings = Settings()
