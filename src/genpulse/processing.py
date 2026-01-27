"""
Task Processing Logic

This module contains the core task processing logic extracted from Worker.
It can be used by both the native Worker and Celery tasks.
"""
import json
import importlib
import os
import asyncio
from typing import Optional
from loguru import logger

from genpulse.handlers.registry import registry
from genpulse.infra.database.manager import DBManager
from genpulse.infra.mq import get_mq
from genpulse.infra.rate_limiter import RateLimiter
from genpulse.config import RATE_LIMITS
from genpulse.types import TaskContext, TaskStatus, EngineError, RateLimitExceeded


class TaskProcessor:
    """
    Processes GenPulse tasks by coordinating handlers, validation, and status updates.
    
    This class is designed to be reusable across different worker runtimes
    (native Worker loop, Celery, etc.).
    """
    
    def __init__(self):
        self.mq = get_mq()
        self.rate_limiter = RateLimiter()
        self._handlers_discovered = False
    
    def _discover_handlers(self):
        """Automatically import all modules in the handlers/ directory to trigger registration"""
        if self._handlers_discovered:
            return
            
        handlers_dir = os.path.join(os.path.dirname(__file__), "handlers")
        if not os.path.exists(handlers_dir):
            logger.warning(f"Handlers directory not found: {handlers_dir}")
            return

        for file in os.listdir(handlers_dir):
            if file.endswith(".py") and file not in ["__init__.py", "base.py", "registry.py"]:
                module_name = file[:-3]
                module_path = f"genpulse.handlers.{module_name}"
                try:
                    importlib.import_module(module_path)
                    logger.info(f"Loaded handlers from {module_path}")
                except Exception as e:
                    logger.error(f"Failed to load handlers from {module_path}: {e}")
        
        self._handlers_discovered = True
        logger.info(f"Registered handlers: {registry.list_handlers()}")
    
    async def process(self, task_json: str) -> Optional[dict]:
        """
        Process a task from its JSON representation.
        
        Args:
            task_json: JSON string containing task data with task_id, task_type, and params.
        
        Returns:
            The task result dict if successful, None otherwise.
            
        Raises:
            RateLimitExceeded: If flow control limits are hit (caller should retry).
        """
        # Ensure handlers are discovered
        self._discover_handlers()
        
        task_data = {}
        try:
            task_data = json.loads(task_json)
        except json.JSONDecodeError:
            logger.error("Failed to decode task JSON")
            return None

        # Rate Limit Check
        params = task_data.get("params", {})
        provider = params.get("provider", "default")
        limit = RATE_LIMITS.get(provider, RATE_LIMITS.get("default", 10.0))
        
        if not await self.rate_limiter.acquire(provider, limit):
            logger.warning(f"Rate limit exceeded for {provider}. Requesting retry.")
            raise RateLimitExceeded(provider)

        try:
            task_id = task_data.get("task_id")
            task_type = task_data.get("task_type")

            # Helper to allow handler/engine to update status/progress
            async def update_status_func(status: str, progress: int = None, result: dict = None):
                # Update MQ Cache for real-time status query
                await self.mq.update_task_status(task_id, status, result=result, progress=progress)
                # Update DB for persistence
                try:
                    await DBManager.update_task(task_id, status, progress=progress, result=result)
                except Exception as e:
                    logger.error(f"Failed to update task {task_id} in DB: {e}")

            context = TaskContext(
                task_id=task_id,
                update_status=update_status_func
            )

            logger.info(f"Processing task {task_id} ({task_type})")

            HandlerClass = registry.get_handler(task_type)
            if not HandlerClass:
                logger.error(f"No handler registered for type: {task_type}")
                await context.set_failed(f"Handler for {task_type} not found")
                return None

            # Update status to processing (init)
            await context.set_processing(progress=0, info="Started")

            handler = HandlerClass()
            
            # 1. Validate
            if not handler.validate_params(params):
                logger.error(f"Validation failed for task {task_id}")
                await context.set_failed("Parameter validation failed")
                return None

            # 2. Execute
            result = await handler.execute(task_data, context)
            
            # Final completion update
            await update_status_func(TaskStatus.COMPLETED, progress=100, result=result)
            logger.info(f"Task {task_id} completed successfully")
            
            return result

        except Exception as e:
            # Allow rate limit exceptions to bubble up for retry
            if isinstance(e, RateLimitExceeded):
                raise e

            msg = str(e)
            logger.exception(f"Failed to process task: {msg}")
            
            # Attempt to update status to failed if we have a task_id
            if 'task_id' in locals() and task_data:
                try:
                    # If it's an EngineError, we might have more details
                    error_details = {"error": msg}
                    if isinstance(e, EngineError):
                        error_details.update(e.details)
                        error_details["provider"] = e.provider
                    
                    await self.mq.update_task_status(task_data["task_id"], TaskStatus.FAILED, result=error_details)
                    await DBManager.update_task(task_data["task_id"], TaskStatus.FAILED, result=error_details)
                except Exception as db_err:
                    logger.error(f"Double fault: failed to update fail status in DB: {db_err}")
            
            return None
