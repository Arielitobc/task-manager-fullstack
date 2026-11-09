from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "local"
    database_url: str = "sqlite:///./tasks.db"
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    redis_url: str = "redis://localhost:6379/0"

    rate_limit_enabled: bool = True
    rate_limit_default: str = "100/minute"
    rate_limit_login: str = "5/minute"
    # Empty -> in-memory storage (single process). Use Redis when running several workers.
    rate_limit_storage_url: str = ""

    # Celery runs tasks inline when true (tests / no Redis available).
    celery_task_always_eager: bool = False

    cors_origins: list[str] = ["http://localhost:5173"]


@lru_cache
def get_settings() -> Settings:
    return Settings()
