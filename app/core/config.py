from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Async Task Service"
    app_version: str = "0.1.0"
    api_prefix: str = "/api/v1"

    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@db:5432/tasks",
        validation_alias="DATABASE_URL",
    )
    database_echo: bool = Field(default=False)

    rabbitmq_url: str = Field(
        default="amqp://guest:guest@rabbitmq:5672/",
        validation_alias="RABBITMQ_URL",
    )
    rabbitmq_queue: str = Field(default="task_queue")
    rabbitmq_max_priority: int = Field(default=10)
    worker_concurrency: int = Field(default=4)
    worker_prefetch_count: int = Field(default=4)

    default_page_size: int = Field(default=20)
    max_page_size: int = Field(default=100)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="APP_",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

