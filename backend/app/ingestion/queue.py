import asyncio
import logging
from typing import Dict, Any, Optional
from backend.app.graph.workflow import run_recovery_workflow

logger = logging.getLogger("reviveai.ingestion.queue")

class EventQueue:
    """
    In-memory Event Queue (4.1.4) feeding the Detector & LangGraph recovery pipeline.
    """
    def __init__(self, maxsize: int = 1000):
        self._queue: asyncio.Queue = asyncio.Queue(maxsize=maxsize)
        self._processed_count: int = 0
        self._failed_count: int = 0
        self._worker_task: Optional[asyncio.Task] = None
        self._running: bool = False

    async def enqueue(self, event: Dict[str, Any]) -> bool:
        """
        Enqueues a normalized event for asynchronous processing.
        """
        try:
            self._queue.put_nowait(event)
            logger.info(f"[Event Queue] Enqueued event '{event.get('event_id')}' (Queue Size: {self._queue.qsize()})")
            return True
        except asyncio.QueueFull:
            logger.error("[Event Queue] Queue is FULL! Dropping event.")
            return False

    async def start_worker(self):
        """
        Starts the background worker consuming from the event queue.
        """
        if self._running:
            return
        self._running = True
        self._worker_task = asyncio.create_task(self._worker_loop())
        logger.info("[Event Queue] Background queue worker started.")

    async def stop_worker(self):
        """
        Stops the background worker gracefully.
        """
        self._running = False
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
        logger.info("[Event Queue] Background queue worker stopped.")

    async def _worker_loop(self):
        while self._running:
            try:
                event = await self._queue.get()
                logger.info(f"[Event Queue Worker] Processing event '{event.get('event_id')}'...")
                try:
                    await run_recovery_workflow(event)
                    self._processed_count += 1
                except Exception as ex:
                    logger.error(f"[Event Queue Worker] Failure processing event {event.get('event_id')}: {ex}")
                    self._failed_count += 1
                finally:
                    self._queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[Event Queue Worker] Unexpected error in worker loop: {e}")
                await asyncio.sleep(0.5)

    def get_status(self) -> Dict[str, Any]:
        """
        Returns queue status & performance metrics.
        """
        return {
            "queue_size": self._queue.qsize(),
            "processed_count": self._processed_count,
            "failed_count": self._failed_count,
            "worker_active": self._running
        }

# Global singleton event queue instance
event_queue = EventQueue()
