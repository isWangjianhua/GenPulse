"""
Celery tasks for GenPulse.

This module defines Celery tasks that wrap the TaskProcessor logic.
"""
import asyncio
from genpulse.infra.mq.celery_app import celery_app
from genpulse.processing import TaskProcessor


from celery.exceptions import MaxRetriesExceededError
from loguru import logger
from genpulse import config
from genpulse.types import RateLimitExceeded, TransientError

@celery_app.task(name="genpulse.tasks.log_failure", queue=config.DLQ_QUEUE_NAME)
def log_failure(task_json: str, error_msg: str):
    """
    Task that resides in the DLQ. 
    It logs the failure and updates the database to reflect the failure.
    """
    logger.error(f"DLQ: Task permanently failed. Error: {error_msg}")
    
    # Update DB status to FAILED
    try:
        import json
        import asyncio
        from genpulse.infra.database.engine import async_session
        from genpulse.infra.database.models import Task
        from sqlalchemy import update

        data = json.loads(task_json)
        task_id = data.get("task_id")
        
        async def _update_db():
            async with async_session() as session:
                stmt = (
                    update(Task)
                    .where(Task.task_id == task_id)
                    .values(status="failed", result={"error": error_msg})
                )
                await session.execute(stmt)
                await session.commit()

        if task_id:
            # Run async DB update in sync task
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            loop.run_until_complete(_update_db())
            logger.info(f"Marked task {task_id} as failed in DB")
            
    except Exception as e:
        logger.error(f"Failed to update task status in DLQ handler: {e}")

    return {"status": "failed", "error": error_msg}

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
        try:
            raise self.retry(exc=exc, countdown=backoff, max_retries=3)
        except MaxRetriesExceededError:
            logger.error(f"Task {self.request.id} max retries exceeded. Moving to DLQ.")
            celery_app.send_task(
                "genpulse.tasks.log_failure",
                args=[task_json, f"Max retries exceeded: {str(exc)}"],
                queue=config.DLQ_QUEUE_NAME
            )
            raise
    except Exception as exc:
        # Unexpected errors -> DLQ immediately
        logger.error(f"Task {self.request.id} failed with unexpected error. Moving to DLQ.")
        celery_app.send_task(
            "genpulse.tasks.log_failure", 
            args=[task_json, f"Unexpected error: {str(exc)}"],
            queue=config.DLQ_QUEUE_NAME
        )
        raise
