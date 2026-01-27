"""
Celery tasks for GenPulse.

This module defines Celery tasks that wrap the TaskProcessor logic.
"""
import asyncio
from genpulse.infra.mq.celery_app import celery_app
from genpulse.processing import TaskProcessor


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
    loop = asyncio.get_event_loop()
    if loop.is_running():
        # If loop is already running, create a new one
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    try:
        result = loop.run_until_complete(processor.process(task_json))
        return result
    finally:
        # Don't close the loop as it might be reused
        pass
