import abc
from typing import Optional, Dict, Any

class BaseMQ(abc.ABC):
    @abc.abstractmethod
    async def ping(self) -> bool:
        """Check connection to the message queue provider."""
        pass

    @abc.abstractmethod
    async def push_task(self, task_data: str):
        """Push a JSON task string into the queue."""
        pass

    @abc.abstractmethod
    async def pop_task(self, timeout: int = 1) -> Optional[tuple]:
        """Pop a task from the queue (blocking or non-blocking)."""
        pass

    @abc.abstractmethod
    async def publish_event(self, task_id: str, event_data: dict):
        """Publish a real-time event (e.g., progress update) to a channel."""
        pass

    @abc.abstractmethod
    async def update_task_status(self, task_id: str, status: str, result: dict = None, progress: int = None):
        """Update task status in the temporary cache/storage of the MQ."""
        pass

    @abc.abstractmethod
    async def get_task_status(self, task_id: str) -> Optional[dict]:
        """Retrieve task status from the MQ cache."""
        pass

    @abc.abstractmethod
    async def close(self):
        """Close connection to the MQ provider."""
        pass

    async def send_task_wait(self, task_data: Dict[str, Any], timeout: int = 60) -> Dict[str, Any]:
        """
        Send a task and wait for its completion (RPC style).
        
        Args:
            task_data: Task payload dict.
            timeout: Max wait time in seconds.
            
        Returns:
            The final result dict.
        """
        raise NotImplementedError("RPC mode not implemented for this MQ backend")

