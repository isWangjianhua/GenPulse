import asyncio
from loguru import logger
from genpulse.infra.mq import get_mq
from genpulse.processing import TaskProcessor
from genpulse.types import RateLimitExceeded

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
                        try:
                            await self.processor.process(task_json)
                        except RateLimitExceeded as rle:
                            logger.warning(f"Rate limit hit for {rle.provider}. Re-queueing after {rle.retry_after}s...")
                            await asyncio.sleep(rle.retry_after)
                            await self.mq.push_task(task_json)

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
