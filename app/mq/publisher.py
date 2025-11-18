from __future__ import annotations

import json
import uuid
from typing import Protocol

import aio_pika
from aio_pika import Message, RobustChannel, RobustConnection

from app.core.config import settings
from app.models import TaskPriority
from app.services.exceptions import PublisherUnavailableError


class TaskPublisherProtocol(Protocol):
    async def connect(self) -> None:
        ...

    async def close(self) -> None:
        ...

    async def publish_task(self, task_id: uuid.UUID, priority: TaskPriority) -> None:
        ...


class TaskQueuePublisher(TaskPublisherProtocol):
    PRIORITY_MAP = {
        TaskPriority.LOW: 2,
        TaskPriority.MEDIUM: 5,
        TaskPriority.HIGH: 9,
    }

    def __init__(
        self,
        url: str | None = None,
        queue_name: str | None = None,
        max_priority: int | None = None,
    ) -> None:
        self.url = url or settings.rabbitmq_url
        self.queue_name = queue_name or settings.rabbitmq_queue
        self.max_priority = max_priority or settings.rabbitmq_max_priority
        self._connection: RobustConnection | None = None
        self._channel: RobustChannel | None = None

    async def connect(self) -> None:
        if self._connection and not self._connection.is_closed:
            return
        self._connection = await aio_pika.connect_robust(self.url)
        self._channel = await self._connection.channel()
        await self._channel.set_qos(prefetch_count=1)
        await self._channel.declare_queue(
            self.queue_name,
            durable=True,
            arguments={"x-max-priority": self.max_priority},
        )

    async def close(self) -> None:
        if self._channel and not self._channel.is_closed:
            await self._channel.close()
        if self._connection and not self._connection.is_closed:
            await self._connection.close()
        self._channel = None
        self._connection = None

    async def publish_task(self, task_id: uuid.UUID, priority: TaskPriority) -> None:
        if self._channel is None:
            raise PublisherUnavailableError("RabbitMQ channel is not available")
        message = Message(
            body=json.dumps({"task_id": str(task_id)}).encode("utf-8"),
            priority=self.PRIORITY_MAP.get(priority, 5),
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            content_type="application/json",
        )
        await self._channel.default_exchange.publish(message, routing_key=self.queue_name)

