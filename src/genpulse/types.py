from dataclasses import dataclass
from typing import Any, Dict, Optional, Callable, Awaitable, List, Literal
from enum import Enum
from pydantic import BaseModel, Field

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

class RateLimitExceeded(GenPulseError):
    """Raised when flow control limits are hit"""
    def __init__(self, provider: str, retry_after: int = 1):
        self.provider = provider
        self.retry_after = retry_after
        super().__init__(f"Rate limit exceeded for {provider}")

class TaskParams(BaseModel):
    """
    Universal parameter schema derived from client patterns (Kling, Volcengine, etc.).
    Serves as a "surface-level" standard.
    """
    # Core Identity
    model: str = Field(..., description="Model identifier (e.g. 'kling-v1', 'wan2.5')")
    
    # Input Content
    prompt: Optional[str] = Field(None, description="Main text prompt")
    negative_prompt: Optional[str] = Field(None, description="Negative text prompt")
    image_urls: Optional[List[str]] = Field(default_factory=list, description="List of input image URLs")
    
    # Generation Configuration
    width: Optional[int] = None
    height: Optional[int] = None
    aspect_ratio: Optional[str] = None
    duration: Optional[int] = None
    num_outputs: int = Field(1, ge=1)
    
    # Advanced / Provider Specific
    seed: Optional[int] = None
    cfg_scale: Optional[float] = None
    
    # Extensibility
    extra: Dict[str, Any] = Field(default_factory=dict, description="Provider-specific extra parameters")
    class Config:
        extra = "allow" # Allow top-level extra fields for convenience

class TaskRequest(BaseModel):
    task_type: str = Field(..., description="Task type (e.g. text-to-video, image-to-video)")
    provider: str = Field(..., description="Service provider (e.g. kling, volcengine)")
    
    params: TaskParams
    
    priority: str = "normal"
    callback_url: Optional[str] = None
