from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Task Service"
    app_version: str = "0.1.0"
    api_prefix: str = "/api/v1"

    # Прямые поля без префиксов и алиасов: читаются из DATABASE_URL, RABBITMQ_URL и т.д.
    database_url: str = "postgresql+asyncpg://postgres:postgres@db:5432/tasks"
    database_echo: bool = False

    rabbitmq_url: str = "amqp://guest:guest@rabbitmq:5672/"
    rabbitmq_queue: str = "task_queue"
    rabbitmq_max_priority: int = 10
    worker_concurrency: int = 4
    worker_prefetch_count: int = 4

    default_page_size: int = 20
    max_page_size: int = 100

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

