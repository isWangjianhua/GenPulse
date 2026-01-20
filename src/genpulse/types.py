from dataclasses import dataclass
from typing import Any, Dict, Optional, Callable, Awaitable
from enum import Enum

class TaskStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class TaskContext:
    """
    Formalized context for task execution.
    Provides structured access to status updates and task metadata.
    """
    task_id: str
    update_status: Callable[[str, Optional[int], Optional[Dict[str, Any]]], Awaitable[None]]
    user_id: Optional[str] = None
    
    async def set_processing(self, progress: int, info: str = None):
        result = {"info": info} if info else None
        await self.update_status(TaskStatus.PROCESSING, progress, result)

    async def set_failed(self, error: str):
        await self.update_status(TaskStatus.FAILED, None, {"error": error})

class GenPulseError(Exception):
    """Base error for GenPulse"""
    pass

class EngineError(GenPulseError):
    """Errors occurring within generation engines"""
    def __init__(self, message: str, provider: str = None, details: Dict[str, Any] = None):
        self.message = message
        self.provider = provider
        self.details = details or {}
        super().__init__(self.message)

class ValidationError(GenPulseError):
    """Errors during parameter validation"""
    pass
