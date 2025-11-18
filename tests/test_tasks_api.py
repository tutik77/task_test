from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.models import TaskPriority


@pytest.mark.asyncio
async def test_create_and_get_task(client: AsyncClient) -> None:
    payload = {
        "title": "Test task",
        "description": "Process payload",
        "priority": TaskPriority.HIGH.value,
    }
    create_response = await client.post("/api/v1/tasks", json=payload)
    assert create_response.status_code == 201
    created = create_response.json()
    assert created["status"] == "PENDING"
    task_id = created["id"]

    get_response = await client.get(f"/api/v1/tasks/{task_id}")
    assert get_response.status_code == 200
    fetched = get_response.json()
    assert fetched["title"] == payload["title"]
    assert fetched["priority"] == TaskPriority.HIGH.value


@pytest.mark.asyncio
async def test_list_tasks_with_filters(client: AsyncClient) -> None:
    for priority in (TaskPriority.LOW, TaskPriority.MEDIUM, TaskPriority.HIGH):
        payload = {"title": f"{priority.value} task", "priority": priority.value}
        response = await client.post("/api/v1/tasks", json=payload)
        assert response.status_code == 201

    list_response = await client.get("/api/v1/tasks?priority=HIGH&limit=2&offset=0")
    assert list_response.status_code == 200
    data = list_response.json()
    assert data["total"] >= 1
    assert all(item["priority"] == "HIGH" for item in data["items"])


@pytest.mark.asyncio
async def test_cancel_task(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/tasks",
        json={"title": "Cancelable task", "priority": TaskPriority.MEDIUM.value},
    )
    task_id = response.json()["id"]

    cancel_response = await client.delete(f"/api/v1/tasks/{task_id}")
    assert cancel_response.status_code == 200
    assert cancel_response.json()["status"] == "CANCELLED"

    status_response = await client.get(f"/api/v1/tasks/{task_id}/status")
    assert status_response.status_code == 200
    assert status_response.json()["status"] == "CANCELLED"

