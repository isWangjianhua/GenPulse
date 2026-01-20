import asyncio
import json
import importlib
import os
from loguru import logger
from genpulse.infra.mq import get_mq
from genpulse.features.registry import registry
from genpulse.infra.database.manager import DBManager

class Worker:
    def __init__(self):
        self.mq = get_mq()
        self.should_run = True

    def _discover_handlers(self):
        """Automatically import all modules in the features/ directory to trigger registration"""
        features_dir = os.path.join(os.path.dirname(__file__), "features")
        for root, dirs, files in os.walk(features_dir):
            for file in files:
                if file.endswith("_handlers.py") or file == "handlers.py":
                    # Construct module path
                    rel_path = os.path.relpath(os.path.join(root, file), os.path.dirname(__file__))
                    module_path = "genpulse." + rel_path.replace(os.path.sep, ".").replace(".py", "")
                    try:
                        importlib.import_module(module_path)
                        logger.info(f"Loaded handlers from {module_path}")
                    except Exception as e:
                        logger.error(f"Failed to load handlers from {module_path}: {e}")

    async def run(self):
        logger.info("Worker starting...")
        self._discover_handlers()
        
        logger.info(f"Registered handlers: {registry.list_handlers()}")

        try:
            while self.should_run:
                try:
                    # brpop returns (queue_name, data)
                    result = await self.mq.pop_task(timeout=1)
                    if result:
                        _, task_json = result
                        await self.process_task(task_json)
                except Exception as e:
                    if self.should_run:
                        logger.error(f"Error in worker loop: {e}")
                        await asyncio.sleep(1)
        finally:
            await self.mq.close()
            logger.info("Worker shut down.")

    def stop(self):
        self.should_run = False

    async def process_task(self, task_json: str):
        from genpulse.types import TaskContext, TaskStatus, EngineError
        
        task_data = {}
        try:
            task_data = json.loads(task_json)
            task_id = task_data.get("task_id")
            task_type = task_data.get("task_type")
            params = task_data.get("params", {})

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
                return

            # Update status to processing (init)
            await context.set_processing(progress=0, info="Started")

            handler = HandlerClass()
            
            # 1. Validate
            if not handler.validate_params(params):
                logger.error(f"Validation failed for task {task_id}")
                await context.set_failed("Parameter validation failed")
                return

            # 2. Execute
            result = await handler.execute(task_data, context)
            
            # Final completion update
            await update_status_func(TaskStatus.COMPLETED, progress=100, result=result)
            logger.info(f"Task {task_id} completed successfully")

        except Exception as e:
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

# The Worker class is now used by worker/__main__.py or other entry points.


