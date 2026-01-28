"""
Celery tasks for GenPulse.

This module defines Celery tasks that wrap the TaskProcessor logic.
"""
import asyncio
from genpulse.infra.mq.celery_app import celery_app
from genpulse.processing import TaskProcessor


from genpulse.types import RateLimitExceeded, TransientError

@celery_app.task(name="genpulse.tasks.execute_task", bind=True)
def execute_task(self, task_json: str):
    """
    Execute a GenPulse task via Celery.
    
    Args:
        task_json: JSON string containing task data.
    
    Returns:
        Task result dict or None if failed.
    """
    processor = TaskProcessor()
    
    # Run async processing in sync context
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    try:
        result = loop.run_until_complete(processor.process(task_json))
        return result
    except RateLimitExceeded as exc:
        # If rate limit hit, retry task with specific delay
        raise self.retry(exc=exc, countdown=exc.retry_after)
    except TransientError as exc:
        # Exponential backoff: 2, 4, 8, 16...
        backoff = exc.retry_after * (2 ** self.request.retries)
        raise self.retry(exc=exc, countdown=backoff, max_retries=3)
    finally:
        pass
