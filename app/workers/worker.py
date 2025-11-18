from __future__ import annotations

import asyncio
import json
import uuid

import aio_pika
from aio_pika import IncomingMessage
import logging

from app.core.config import settings
from app.db import async_session_factory
from app.repositories import TaskRepository
from app.services.worker_service import TaskWorkerService
from app.workers.processor import TaskProcessor

logger = logging.getLogger(__name__)


class QueueWorker:
    def __init__(
        self,
        queue_name: str | None = None,
        url: str | None = None,
        concurrency: int | None = None,
        prefetch_count: int | None = None,
    ) -> None:
        self.queue_name = queue_name or settings.rabbitmq_queue
        self.url = url or settings.rabbitmq_url
        self.concurrency = concurrency or settings.worker_concurrency
        self.prefetch_count = prefetch_count or settings.worker_prefetch_count
        self.processor = TaskProcessor()
        self._connection: aio_pika.RobustConnection | None = None
        self._channel: aio_pika.RobustChannel | None = None

    async def start(self) -> None:
        self._connection = await aio_pika.connect_robust(self.url)
        self._channel = await self._connection.channel()
        await self._channel.set_qos(prefetch_count=self.prefetch_count)
        queue = await self._channel.declare_queue(
            self.queue_name,
            durable=True,
            arguments={"x-max-priority": settings.rabbitmq_max_priority},
        )
        semaphore = asyncio.Semaphore(self.concurrency)
        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                await semaphore.acquire()
                asyncio.create_task(self._process_message(message, semaphore))

    async def close(self) -> None:
        if self._channel and not self._channel.is_closed:
            await self._channel.close()
        if self._connection and not self._connection.is_closed:
            await self._connection.close()

    async def _process_message(
        self,
        message: IncomingMessage,
        semaphore: asyncio.Semaphore,
    ) -> None:
        try:
            async with message.process(requeue=False):
                try:
                    payload = json.loads(message.body.decode("utf-8"))
                    task_id = uuid.UUID(payload["task_id"])
                except (ValueError, KeyError) as exc:
                    logger.error("Invalid task payload: %s", exc)
                    return
                await self._handle_task(task_id)
        finally:
            semaphore.release()

    async def _handle_task(self, task_id: uuid.UUID) -> None:
        try:
            async with async_session_factory() as session:
                repo = TaskRepository(session)
                service = TaskWorkerService(session, repo, self.processor)
                await service.execute(task_id)
        except Exception as exc:
            logger.exception("Worker failed to execute task %s: %s", task_id, exc)

