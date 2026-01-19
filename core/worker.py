import asyncio
import json
import logging
import importlib
import os
from core.mq import RedisManager
from core.registry import registry
from core.db_manager import DBManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Worker")

class Worker:
    def __init__(self):
        self.redis_mgr = RedisManager()
        self.should_run = True

    def _discover_handlers(self):
        """Automatically import all modules in the handlers/ directory to trigger registration"""
        handler_dir = "handlers"
        for filename in os.listdir(handler_dir):
            if filename.endswith(".py") and filename != "base.py" and not filename.startswith("__"):
                module_name = f"handlers.{filename[:-3]}"
                try:
                    importlib.import_module(module_name)
                    logger.info(f"Discovered handler module: {module_name}")
                except Exception as e:
                    logger.error(f"Failed to load handler {module_name}: {e}")

    async def run(self):
        # Local ComfyUI Management
        from core.config import settings
        from core.process_manager import ComfyProcessManager
        
        comfy_mgr = None
        if settings.COMFY_ENABLE_LOCAL:
            comfy_mgr = ComfyProcessManager(port=settings.COMFY_PORT)
            try:
                comfy_mgr.start(cpu_only=settings.COMFY_CPU_ONLY)
            except Exception as e:
                logger.warning(f"Could not start local ComfyUI: {e}")

        logger.info("Worker starting...")
        self._discover_handlers()
        
        logger.info(f"Registered handlers: {registry.list_handlers()}")

        while self.should_run:
            try:
                # brpop returns (queue_name, data)
                result = await self.redis_mgr.pop_task(timeout=1)
                if result:
                    _, task_json = result
                    await self.process_task(task_json)
            except Exception as e:
                logger.error(f"Error in worker loop: {e}")
                await asyncio.sleep(1)

    async def process_task(self, task_json: str):
        try:
            task_data = json.loads(task_json)
            task_id = task_data.get("task_id")
            task_type = task_data.get("task_type")
            params = task_data.get("params", {})

            logger.info(f"Processing task {task_id} of type {task_type}")

            HandlerClass = registry.get_handler(task_type)
            if not HandlerClass:
                logger.error(f"No handler registered for type: {task_type}")
                await self.redis_mgr.update_task_status(task_id, "failed", result={"error": "Handler not found"})
                return

            # Update status to processing
            await self.redis_mgr.update_task_status(task_id, "processing", progress=0)

            handler = HandlerClass()
            
            # Helper to allow handler to update status/progress
            async def update_status(status: str, progress: int = None, result: dict = None):
                # Update Redis
                await self.redis_mgr.update_task_status(task_id, status, result=result, progress=progress)
                # Update DB
                try:
                    await DBManager.update_task(task_id, status, progress=progress, result=result)
                except Exception as e:
                    logger.error(f"Failed to update task {task_id} in DB: {e}")

            # 1. Validate
            if not handler.validate_params(params):
                logger.error(f"Validation failed for task {task_id}")
                await update_status("failed", result={"error": "Validation failed"})
                return

            # 2. Execute
            context = {
                "task_id": task_id,
                "update_status": update_status
            } 
            result = await handler.execute(task_data, context)
            
            # Final completion update
            await update_status("completed", progress=100, result=result)
            logger.info(f"Task {task_id} completed successfully")

        except Exception as e:
            logger.error(f"Failed to process task: {e}")
            if 'task_id' in locals():
                await self.redis_mgr.update_task_status(task_id, "failed", result={"error": str(e)})

if __name__ == "__main__":
    worker = Worker()
    asyncio.run(worker.run())
