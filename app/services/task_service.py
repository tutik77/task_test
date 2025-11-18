from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Task, TaskPriority, TaskStatus
from app.mq import TaskPublisherProtocol
from app.repositories import TaskRepository
from app.schemas import TaskCreate
from app.services.exceptions import (
    PublisherUnavailableError,
    TaskConflictError,
    TaskNotFoundError,
)


class TaskService:
    TERMINAL_STATUSES = {
        TaskStatus.COMPLETED,
        TaskStatus.FAILED,
        TaskStatus.CANCELLED,
    }

    def __init__(
        self,
        session: AsyncSession,
        repository: TaskRepository,
        publisher: TaskPublisherProtocol | None,
    ) -> None:
        self.session = session
        self.repository = repository
        self.publisher = publisher

    async def create_task(self, payload: TaskCreate) -> Task:
        publisher = self.publisher
        if publisher is None:
            raise PublisherUnavailableError("Publisher is not available")
        task = await self.repository.add(
            title=payload.title,
            description=payload.description,
            priority=payload.priority,
        )
        try:
            await publisher.publish_task(task.id, task.priority)
        except PublisherUnavailableError:
            await self.session.rollback()
            raise
        except Exception as exc:
            await self.session.rollback()
            raise PublisherUnavailableError("Failed to publish task to queue") from exc
        await self.repository.mark_status(task, status=TaskStatus.PENDING)
        await self.session.commit()
        await self.session.refresh(task)
        return task

    async def list_tasks(
        self,
        *,
        status: TaskStatus | None,
        priority: TaskPriority | None,
        limit: int,
        offset: int,
    ) -> tuple[list[Task], int]:
        return await self.repository.list(
            status=status,
            priority=priority,
            limit=limit,
            offset=offset,
        )

    async def get_task(self, task_id: uuid.UUID) -> Task:
        task = await self.repository.get(task_id)
        if task is None:
            raise TaskNotFoundError
        return task

    async def cancel_task(self, task_id: uuid.UUID) -> Task:
        task = await self.repository.get(task_id)
        if task is None:
            raise TaskNotFoundError
        if task.status in self.TERMINAL_STATUSES:
            raise TaskConflictError("Task already completed")
        now = datetime.now(tz=timezone.utc)
        await self.repository.mark_status(
            task,
            status=TaskStatus.CANCELLED,
            finished_at=now,
        )
        await self.session.commit()
        await self.session.refresh(task)
        return task

