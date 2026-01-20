from typing import Optional, List, Union, Literal, Dict, Any
from pydantic import BaseModel, Field

# --- Request Schemas ---

class DashScopeImageParams(BaseModel):
    """DashScope Image Generation Parameters"""
    model: str = Field(..., description="Model ID, e.g., 'qwen-image-plus'")
    prompt: str = Field(..., min_length=1, max_length=500)
    negative_prompt: Optional[str] = " "
    n: int = Field(1, ge=1, le=4)
    size: str = Field("1024*1024", description="Image resolution, e.g., '1024*1024'")
    seed: Optional[int] = Field(None, ge=0, le=4294967290)
    style: Optional[str] = "<auto>"
    prompt_extend: bool = True
    watermark: bool = False
    
    class Config:
        extra = "allow"

class DashScopeMessageContent(BaseModel):
    """Content item for MultiModalConversation"""
    image: Optional[str] = None
    text: Optional[str] = None

class DashScopeMessage(BaseModel):
    """Message structure for MultiModalConversation"""
    role: str = "user"
    content: List[DashScopeMessageContent]

class DashScopeImageEditParams(BaseModel):
    """DashScope Image Edit Parameters (MultiModalConversation)"""
    model: str = Field(..., description="Model ID, e.g., 'qwen-image-edit-max'")
    messages: List[DashScopeMessage]
    n: int = Field(1, ge=1, le=6)
    size: str = Field("1024*1024")
    negative_prompt: Optional[str] = " "
    prompt_extend: bool = True
    watermark: bool = False
    
    class Config:
        extra = "allow"

class DashScopeVideoParams(BaseModel):
    """DashScope Video Generation Parameters"""
    model: str = Field(..., description="Model ID, e.g., 'wan2.5-t2v-preview'")
    prompt: str = Field(..., min_length=1)
    resolution: Optional[Literal["480P", "720P", "1080P"]] = None
    size: Optional[str] = Field(None, description="Resolution e.g. '832*480'")
    duration: Optional[int] = Field(None, description="Video duration in seconds")
    audio_url: Optional[str] = Field(None, description="Audio file URL to synch with the video")
    negative_prompt: Optional[str] = None
    seed: Optional[int] = None
    first_frame_url: Optional[str] = None
    last_frame_url: Optional[str] = None
    prompt_extend: bool = True
    watermark: bool = False
    
    class Config:
        extra = "allow"

# --- Response Schemas ---

class DashScopeImageItem(BaseModel):
    """Single generated image item"""
    url: Optional[str] = None

class DashScopeUsage(BaseModel):
    """Usage information"""
    image_count: int = 0

class DashScopeStatusResponse(BaseModel):
    """Complete response model for DashScope Task Status (Unified for Image/Video)"""
    task_id: Optional[str] = Field(None, description="Task ID")
    task_status: Optional[str] = Field(None, description="Current status")
    results: Optional[List[DashScopeImageItem]] = None
    video_url: Optional[str] = None
    usage: Optional[Any] = None
    message: Optional[str] = None
    code: Optional[str] = None

    @property
    def is_finished(self) -> bool:
        return self.task_status in ["SUCCEEDED", "FAILED", "CANCELED"]

    @property
    def is_succeeded(self) -> bool:
        return self.task_status == "SUCCEEDED"

