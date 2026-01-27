import asyncio
from loguru import logger
from genpulse.infra.mq import get_mq
from genpulse.processing import TaskProcessor

class Worker:
    def __init__(self):
        self.mq = get_mq()
        self.processor = TaskProcessor()
        self.should_run = True

    async def run(self):
        logger.info("Worker starting...")
        
        try:
            while self.should_run:
                try:
                    # brpop returns (queue_name, data)
                    result = await self.mq.pop_task(timeout=1)
                    if result:
                        _, task_json = result
                        await self.processor.process(task_json)
                except Exception as e:
                    if self.should_run:
                        logger.error(f"Error in worker loop: {e}")
                        await asyncio.sleep(1)
        finally:
            await self.mq.close()
            logger.info("Worker shut down.")

    def stop(self):
        self.should_run = False

# The Worker class is now used by worker/__main__.py or other entry points.
