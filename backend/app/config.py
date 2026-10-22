from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # backend/.env, wherever the process starts (Passenger, manage.py over SSH, uvicorn)
    model_config = SettingsConfigDict(env_file=Path(__file__).resolve().parent.parent / ".env", extra="ignore")

    database_url: str = "postgresql+psycopg://smart:smart@localhost:5432/smart_storage"
    bot_token: str = ""
    jwt_secret: str = "change-me"
    jwt_ttl_hours: int = 24
    init_data_max_age_seconds: int = 24 * 3600
    webapp_url: str = ""
    # Public URL of the API; the bot receives updates at {api_url}/telegram/webhook
    api_url: str = ""
    webhook_secret: str = ""
    cors_origins: list[str] = ["http://localhost:5173"]


@lru_cache
def get_settings() -> Settings:
    return Settings()
