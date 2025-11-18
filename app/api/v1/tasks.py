from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import get_task_service
from app.core.config import settings
from app.models import TaskPriority, TaskStatus
from app.schemas import TaskCreate, TaskList, TaskRead, TaskStatusSchema
from app.services import TaskService
from app.services.exceptions import (
    PublisherUnavailableError,
    TaskConflictError,
    TaskNotFoundError,
)

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post(
    "",
    response_model=TaskRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_task(
    payload: TaskCreate,
    service: TaskService = Depends(get_task_service),
) -> TaskRead:
    try:
        task = await service.create_task(payload)
    except PublisherUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    return TaskRead.model_validate(task)


@router.get("", response_model=TaskList)
async def list_tasks(
    status_filter: TaskStatus | None = Query(None, alias="status"),
    priority_filter: TaskPriority | None = Query(None, alias="priority"),
    limit: int = Query(
        default=settings.default_page_size,
        ge=1,
        le=settings.max_page_size,
    ),
    offset: int = Query(default=0, ge=0),
    service: TaskService = Depends(get_task_service),
) -> TaskList:
    tasks, total = await service.list_tasks(
        status=status_filter,
        priority=priority_filter,
        limit=limit,
        offset=offset,
    )
    return TaskList(
        items=[TaskRead.model_validate(task) for task in tasks],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{task_id}", response_model=TaskRead)
async def get_task(
    task_id: uuid.UUID,
    service: TaskService = Depends(get_task_service),
) -> TaskRead:
    try:
        task = await service.get_task(task_id)
    except TaskNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found") from exc
    return TaskRead.model_validate(task)


@router.delete("/{task_id}", response_model=TaskRead)
async def cancel_task(
    task_id: uuid.UUID,
    service: TaskService = Depends(get_task_service),
) -> TaskRead:
    try:
        task = await service.cancel_task(task_id)
    except TaskNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found") from exc
    except TaskConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return TaskRead.model_validate(task)


@router.get("/{task_id}/status", response_model=TaskStatusSchema)
async def get_task_status(
    task_id: uuid.UUID,
    service: TaskService = Depends(get_task_service),
) -> TaskStatusSchema:
    try:
        task = await service.get_task(task_id)
    except TaskNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found") from exc
    return TaskStatusSchema(status=task.status)

