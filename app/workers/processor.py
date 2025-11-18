from __future__ import annotations

import asyncio

from app.models import Task, TaskPriority


class TaskProcessor:
    DURATION_MAP = {
        TaskPriority.HIGH: 0.05,
        TaskPriority.MEDIUM: 0.1,
        TaskPriority.LOW: 0.15,
    }

    async def run(self, task: Task) -> dict:
        delay = self.DURATION_MAP.get(task.priority, 0.1)
        await asyncio.sleep(delay)
        return {
            "summary": f"Task {task.id} processed",
            "title": task.title,
            "priority": task.priority.value,
        }

