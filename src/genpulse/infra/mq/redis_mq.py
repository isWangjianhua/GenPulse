import json
import time
import redis.asyncio as redis
from typing import Optional
from genpulse.infra.mq.base import BaseMQ
from genpulse import config

class RedisMQ(BaseMQ):
    def __init__(self):
        self.redis_url = config.REDIS_URL
        self.client = redis.from_url(self.redis_url, decode_responses=True)
        self.prefix = config.REDIS_PREFIX
        self.queue_name = f"{self.prefix}{config.REDIS_TASK_QUEUE_NAME}"

    async def ping(self) -> bool:
        return await self.client.ping()

    async def push_task(self, task_data: str):
        await self.client.lpush(self.queue_name, task_data)

    async def pop_task(self, timeout: int = 1) -> Optional[tuple]:
        return await self.client.brpop(self.queue_name, timeout=timeout)

    async def publish_event(self, task_id: str, event_data: dict):
        channel = f"{self.prefix}task_updates:{task_id}"
        await self.client.publish(channel, json.dumps(event_data))

    async def update_task_status(self, task_id: str, status: str, result: dict = None, progress: int = None):
        status_key = f"{self.prefix}task_status:{task_id}"
        data = {"status": status, "updated_at": time.time()}
        if result: data["result"] = result
        if progress is not None: data["progress"] = progress
        
        await self.client.set(status_key, json.dumps(data), ex=3600) # Expire in 1 hour
        await self.publish_event(task_id, data)

    async def get_task_status(self, task_id: str) -> Optional[dict]:
        status_key = f"{self.prefix}task_status:{task_id}"
        data = await self.client.get(status_key)
        if data:
            return json.loads(data)
        return None

    async def close(self):
        await self.client.close()

