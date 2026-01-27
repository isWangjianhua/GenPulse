"""
RabbitMQ implementation of BaseMQ using aio-pika.

This implementation uses RabbitMQ for queueing and pub/sub,
but falls back to Redis for state storage (hybrid approach).
"""
import json
import time
from typing import Optional
import aio_pika
from aio_pika import Message, DeliveryMode, ExchangeType
import redis.asyncio as redis

from genpulse.infra.mq.base import BaseMQ
from genpulse import config


class RabbitMQ(BaseMQ):
    """
    RabbitMQ adapter for GenPulse message queue.
    
    Uses RabbitMQ for task queueing and event publishing,
    but uses Redis for task status caching (since RabbitMQ is not a KV store).
    """
    
    def __init__(self):
        self.rabbitmq_url = config.RABBITMQ_URL
        self.queue_name = config.TASK_QUEUE_NAME
        self.connection: Optional[aio_pika.Connection] = None
        self.channel: Optional[aio_pika.Channel] = None
        self.queue: Optional[aio_pika.Queue] = None
        self.exchange: Optional[aio_pika.Exchange] = None
        
        # Redis for status storage
        self.redis_client = redis.from_url(config.REDIS_URL, decode_responses=True)
        self.status_prefix = config.TASK_STATUS_PREFIX
    
    async def _ensure_connection(self):
        """Ensure RabbitMQ connection and channel are established."""
        if self.connection is None or self.connection.is_closed:
            self.connection = await aio_pika.connect_robust(self.rabbitmq_url)
            self.channel = await self.connection.channel()
            await self.channel.set_qos(prefetch_count=1)
            
            # Declare queue
            self.queue = await self.channel.declare_queue(
                self.queue_name,
                durable=True
            )
            
            # Declare exchange for pub/sub
            self.exchange = await self.channel.declare_exchange(
                "genpulse_events",
                ExchangeType.TOPIC,
                durable=True
            )
    
    async def ping(self) -> bool:
        """Check connection to RabbitMQ."""
        try:
            await self._ensure_connection()
            return not self.connection.is_closed
        except Exception:
            return False
    
    async def push_task(self, task_data: str):
        """Push a JSON task string into the RabbitMQ queue."""
        await self._ensure_connection()
        
        message = Message(
            task_data.encode(),
            delivery_mode=DeliveryMode.PERSISTENT
        )
        
        await self.channel.default_exchange.publish(
            message,
            routing_key=self.queue_name
        )
    
    async def pop_task(self, timeout: int = 1) -> Optional[tuple]:
        """
        Pop a task from the queue.
        
        Args:
            timeout: Timeout in seconds (note: aio-pika doesn't support exact timeout like Redis BRPOP).
        
        Returns:
            Tuple of (queue_name, task_data) or None if no message available.
        """
        await self._ensure_connection()
        
        try:
            # Get one message with timeout
            async with self.queue.iterator(timeout=timeout) as queue_iter:
                async for message in queue_iter:
                    async with message.process():
                        return (self.queue_name, message.body.decode())
        except aio_pika.exceptions.QueueEmpty:
            return None
        except Exception:
            return None
    
    async def publish_event(self, task_id: str, event_data: dict):
        """Publish a real-time event to a topic exchange."""
        await self._ensure_connection()
        
        routing_key = f"task.{task_id}"
        message = Message(
            json.dumps(event_data).encode(),
            delivery_mode=DeliveryMode.NOT_PERSISTENT
        )
        
        await self.exchange.publish(
            message,
            routing_key=routing_key
        )
    
    async def update_task_status(self, task_id: str, status: str, result: dict = None, progress: int = None):
        """
        Update task status in Redis cache.
        
        Note: RabbitMQ is not a KV store, so we use Redis for status caching.
        """
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
    
    async def close(self):
        """Close connections to RabbitMQ and Redis."""
        if self.connection and not self.connection.is_closed:
            await self.connection.close()
        await self.redis_client.aclose()
