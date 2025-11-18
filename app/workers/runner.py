from __future__ import annotations

import asyncio
import logging

from app.workers.worker import QueueWorker


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main() -> None:
    worker = QueueWorker()
    logger.info("Starting task worker")
    await worker.start()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Worker shutdown requested")

