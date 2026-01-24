from typing import Optional, List, Union, Literal, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

# --- Request Schemas ---

class DashScopeImageParams(BaseModel):
    """
    Parameters for DashScope image generation task.

    Args:
        model: Model ID (e.g., 'qwen-image-plus').
        prompt: The descriptive prompt for generation.
        size: Image resolution (e.g., '1024*1024').
        n: Number of images to generate (1-4).
    """
    model: str = Field(..., description="Model ID, e.g., 'qwen-image-plus'")
    prompt: str = Field(..., min_length=1, max_length=500, description="Text prompt")
    negative_prompt: Optional[str] = Field(" ", description="Negative prompt to avoid")
    n: int = Field(1, ge=1, le=4, description="Number of images")
    size: str = Field("1024*1024", description="Image resolution")
    seed: Optional[int] = Field(None, ge=0, le=4294967290, description="Random seed")
    style: Optional[str] = Field("<auto>", description="Image style")
    prompt_extend: bool = Field(True, description="Enable prompt enhancement")
    watermark: bool = Field(False, description="Add watermark")
    
    model_config = ConfigDict(extra="allow")

class DashScopeMessageContent(BaseModel):
    """Content item within a MultiModal conversation message."""
    image: Optional[str] = Field(None, description="Image URL")
    text: Optional[str] = Field(None, description="Text content")

class DashScopeMessage(BaseModel):
    """Message structure for MultiModalConversation."""
    role: str = Field("user", description="Role: 'user' or 'system'")
    content: List[DashScopeMessageContent] = Field(..., description="List of content items")

class DashScopeImageEditParams(BaseModel):
    """
    Parameters for DashScope image editing task.

    Uses MultiModalConversation structure.
    """
    model: str = Field(..., description="Model ID, e.g., 'qwen-image-edit-max'")
    messages: List[DashScopeMessage] = Field(..., description="Conversation history including input image")
    n: int = Field(1, ge=1, le=6, description="Number of output images")
    size: str = Field("1024*1024", description="Output resolution")
    negative_prompt: Optional[str] = " "
    prompt_extend: bool = True
    watermark: bool = False
    
    model_config = ConfigDict(extra="allow")

class DashScopeVideoParams(BaseModel):
    """
    Parameters for DashScope video generation task.
    Supports Text-to-Video and Image-to-Video via explicit frame URLs.
    """
    model: str = Field(..., description="Model ID, e.g., 'wan2.5-t2v-preview'")
    prompt: str = Field(..., min_length=1, description="Video description")
    resolution: Optional[Literal["480P", "720P", "1080P"]] = Field(None, description="Video resolution enum")
    size: Optional[str] = Field(None, description="Resolution e.g. '832*480'")
    duration: Optional[int] = Field(None, description="Duration in seconds")
    audio_url: Optional[str] = Field(None, description="Audio file URL to sync")
    negative_prompt: Optional[str] = None
    seed: Optional[int] = None
    first_frame_url: Optional[str] = Field(None, description="Start frame for I2V")
    last_frame_url: Optional[str] = Field(None, description="End frame for I2V")
    prompt_extend: bool = True
    watermark: bool = False
    
    model_config = ConfigDict(extra="allow")

# --- Response Schemas ---

class DashScopeImageItem(BaseModel):
    """
    Single generated image item.
    """
    url: Optional[str] = Field(None, description="Generated image URL")

class DashScopeUsage(BaseModel):
    """
    Usage information.
    """
    image_count: int = Field(0, description="Number of images generated")

class DashScopeStatusResponse(BaseModel):
    """
    Complete response model for DashScope Task Status (Unified for Image/Video).
    """
    task_id: Optional[str] = Field(None, description="Task ID")
    task_status: Optional[str] = Field(None, description="Current status (SUCCEEDED, FAILED, RUNNING)")
    results: Optional[List[DashScopeImageItem]] = Field(None, description="List of generated image results")
    video_url: Optional[str] = Field(None, description="Generated video URL")
    usage: Optional[Any] = Field(None, description="Usage statistics")
    message: Optional[str] = Field(None, description="Error message")
    code: Optional[str] = Field(None, description="Error code")

    @property
    def is_finished(self) -> bool:
        return self.task_status in ["SUCCEEDED", "FAILED", "CANCELED"]

    @property
    def is_succeeded(self) -> bool:
        return self.task_status == "SUCCEEDED"

