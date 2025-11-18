from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator
from typing import Any

import pytest
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.api import api_router
from app.api.deps import get_async_session
from app.db import Base
from app.mq import TaskPublisherProtocol


class DummyPublisher(TaskPublisherProtocol):
    def __init__(self) -> None:
        self.messages: list[dict[str, Any]] = []

    async def connect(self) -> None:
        return None

    async def close(self) -> None:
        return None

    async def publish_task(self, task_id, priority) -> None:
        self.messages.append({"task_id": task_id, "priority": priority})


@pytest.fixture
async def engine():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
async def session_factory(engine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


@pytest.fixture
async def application(session_factory) -> AsyncGenerator[FastAPI, None]:
    app = FastAPI()
    app.include_router(api_router)
    publisher = DummyPublisher()
    app.state.publisher = publisher

    async def override_session() -> AsyncGenerator[AsyncSession, None]:
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_async_session] = override_session
    yield app


@pytest.fixture
async def client(application: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=application)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client

