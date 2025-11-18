from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import TaskStatus
from app.repositories import TaskRepository
from app.workers.processor import TaskProcessor


class TaskWorkerService:
    def __init__(
        self,
        session: AsyncSession,
        repository: TaskRepository,
        processor: TaskProcessor,
    ) -> None:
        self.session = session
        self.repository = repository
        self.processor = processor

    async def execute(self, task_id: uuid.UUID) -> None:
        task = await self.repository.get_for_update(task_id)
        if task is None:
            await self.session.commit()
            return
        if task.status in {
            TaskStatus.CANCELLED,
            TaskStatus.IN_PROGRESS,
            TaskStatus.COMPLETED,
            TaskStatus.FAILED,
        }:
            await self.session.commit()
            return
        start_time = datetime.now(tz=timezone.utc)
        await self.repository.mark_status(
            task,
            status=TaskStatus.IN_PROGRESS,
            started_at=start_time,
        )
        await self.session.commit()
        try:
            result = await self.processor.run(task)
        except Exception as exc:
            finish_time = datetime.now(tz=timezone.utc)
            await self.repository.mark_status(
                task,
                status=TaskStatus.FAILED,
                finished_at=finish_time,
                error=str(exc),
            )
            await self.session.commit()
            return
        finish_time = datetime.now(tz=timezone.utc)
        await self.repository.mark_status(
            task,
            status=TaskStatus.COMPLETED,
            finished_at=finish_time,
            result=result,
            error=None,
        )
        await self.session.commit()

