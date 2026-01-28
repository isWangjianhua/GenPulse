"""
Celery MQ adapter for GenPulse.

This adapter allows GenPulse to use Celery as the task queue backend.
"""
import json
import time
from typing import Optional
import redis.asyncio as redis

from genpulse.infra.mq.base import BaseMQ
from genpulse.infra.mq.celery_app import celery_app
from genpulse import config


class CeleryMQ(BaseMQ):
    """
    Celery adapter for GenPulse message queue.
    
    Uses Celery for task dispatching and Redis for status caching.
    Note: pop_task() is not used with Celery as workers are managed by Celery itself.
    """
    
    def __init__(self):
        # Redis for status storage
        self.redis_client = redis.from_url(config.REDIS_URL, decode_responses=True)
        self.status_prefix = config.TASK_STATUS_PREFIX
    
    async def ping(self) -> bool:
        """Check connection to Celery broker."""
        try:
            # Check if Celery can connect to broker
            celery_app.connection().ensure_connection(max_retries=1)
            return True
        except Exception:
            return False
    
    async def push_task(self, task_data: str):
        """
        Push a task to Celery.
        
        Args:
            task_data: JSON string containing task information.
        """
        # Send task to Celery
        celery_app.send_task(
            "genpulse.tasks.execute_task",
            args=[task_data],
            queue="genpulse_tasks"
        )
    
    async def pop_task(self, timeout: int = 1) -> Optional[tuple]:
        """
        Not used with Celery - workers are managed by Celery itself.
        
        Raises:
            NotImplementedError: This method is not applicable for Celery.
        """
        raise NotImplementedError(
            "pop_task() is not used with Celery. "
            "Start Celery workers using: celery -A genpulse.infra.mq.celery_app worker"
        )
    
    async def publish_event(self, task_id: str, event_data: dict):
        """
        Publish event via Redis pub/sub.
        
        Note: Celery doesn't have built-in pub/sub, so we use Redis.
        """
        channel = f"{config.REDIS_PREFIX}task_updates:{task_id}"
        await self.redis_client.publish(channel, json.dumps(event_data))
    
    async def update_task_status(self, task_id: str, status: str, result: dict = None, progress: int = None):
        """Update task status in Redis cache."""
        status_key = f"{self.status_prefix}{task_id}"
        data = {"status": status, "updated_at": time.time()}
        if result:
            data["result"] = result
        if progress is not None:
            data["progress"] = progress
        
        await self.redis_client.set(status_key, json.dumps(data), ex=3600)  # Expire in 1 hour
        await self.publish_event(task_id, data)
    
    async def get_task_status(self, task_id: str) -> Optional[dict]:
        """Retrieve task status from Redis cache."""
        status_key = f"{self.status_prefix}{task_id}"
        data = await self.redis_client.get(status_key)
        if data:
            return json.loads(data)
        return None

    async def send_task_wait(self, task_data: dict, timeout: int = 60) -> dict:
        """
        Send a task and wait for its completion using Redis Pub/Sub.
        This provides the RPC-like experience.
        """
        task_id = task_data.get("task_id")
        if not task_id:
            raise ValueError("Task data must contain 'task_id'")

        # 1. Subscribe to updates FIRST to avoid race conditions
        pubsub = self.redis_client.pubsub()
        channel = f"{config.REDIS_PREFIX}task_updates:{task_id}"
        await pubsub.subscribe(channel)

        try:
            # 2. Push task
            # Ensure task_data is string for push_task
            payload = json.dumps(task_data) if isinstance(task_data, dict) else task_data
            await self.push_task(payload)
            
            # 3. Wait loop
            start_time = time.time()
            while (time.time() - start_time) < timeout:
                # Poll for message with short timeout
                message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=0.5)
                
                if message:
                    try:
                        data = json.loads(message["data"])
                        status = data.get("status")
                        if status in ["completed", "failed"]:
                            return data
                    except Exception:
                        pass # Ignore malformed messages
                
        except Exception as e:
            raise e
        finally:
            await pubsub.unsubscribe(channel)
            await pubsub.close()
            
        raise TimeoutError(f"Task {task_id} timed out after {timeout}s")

    async def close(self):
        """Close Redis connection."""
        await self.redis_client.aclose()
