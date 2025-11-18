from __future__ import annotations

import uuid
from typing import cast

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Task, TaskPriority, TaskStatus


_UNSET = object()


class TaskRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(
        self,
        *,
        title: str,
        description: str | None,
        priority: TaskPriority,
    ) -> Task:
        task = Task(
            title=title,
            description=description,
            priority=priority,
            status=TaskStatus.NEW,
        )
        self.session.add(task)
        await self.session.flush()
        return task

    async def get(self, task_id: uuid.UUID) -> Task | None:
        return await self.session.get(Task, task_id)

    async def get_for_update(self, task_id: uuid.UUID) -> Task | None:
        stmt = select(Task).where(Task.id == task_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list(
        self,
        *,
        status: TaskStatus | None,
        priority: TaskPriority | None,
        limit: int,
        offset: int,
    ) -> tuple[list[Task], int]:
        stmt = self._apply_filters(select(Task), status=status, priority=priority)
        stmt = stmt.order_by(Task.created_at.desc()).limit(limit).offset(offset)
        items_result = await self.session.execute(stmt)
        items = items_result.scalars().all()

        count_stmt = self._apply_filters(select(func.count(Task.id)), status, priority)
        count_result = await self.session.execute(count_stmt)
        total = count_result.scalar_one() or 0
        return items, total

    async def mark_status(
        self,
        task: Task,
        *,
        status: TaskStatus,
        started_at=None,
        finished_at=None,
        result: dict | None | object = _UNSET,
        error: str | None | object = _UNSET,
    ) -> Task:
        task.status = status
        if started_at is not None:
            task.started_at = started_at
        if finished_at is not None:
            task.finished_at = finished_at
        if result is not _UNSET:
            task.result = cast(dict | None, result)
        if error is not _UNSET:
            task.error = cast(str | None, error)
        await self.session.flush()
        return task

    def _apply_filters(
        self,
        stmt: Select,
        *,
        status: TaskStatus | None,
        priority: TaskPriority | None,
    ) -> Select:
        if status is not None:
            stmt = stmt.where(Task.status == status)
        if priority is not None:
            stmt = stmt.where(Task.priority == priority)
        return stmt

