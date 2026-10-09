from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://smart:smart@localhost:5432/smart_storage"
    bot_token: str = ""
    jwt_secret: str = "change-me"
    jwt_ttl_hours: int = 24
    init_data_max_age_seconds: int = 24 * 3600
    webapp_url: str = ""
    cors_origins: list[str] = ["http://localhost:5173"]


@lru_cache
def get_settings() -> Settings:
    return Settings()
