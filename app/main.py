from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api import api_router
from app.core.config import settings
from app.mq import TaskQueuePublisher


@asynccontextmanager
async def lifespan(app: FastAPI):
    publisher = TaskQueuePublisher()
    await publisher.connect()
    app.state.publisher = publisher
    try:
        yield
    finally:
        await publisher.close()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)
app.include_router(api_router)

