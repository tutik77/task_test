from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_async_session
from app.mq import TaskPublisherProtocol
from app.repositories import TaskRepository
from app.services.task_service import TaskService


async def get_publisher(request: Request) -> TaskPublisherProtocol | None:
    publisher: TaskPublisherProtocol | None = getattr(request.app.state, "publisher", None)
    return publisher


async def get_task_service(
    session: AsyncSession = Depends(get_async_session),
    publisher: TaskPublisherProtocol | None = Depends(get_publisher),
) -> TaskService:
    repository = TaskRepository(session)
    return TaskService(session=session, repository=repository, publisher=publisher)

