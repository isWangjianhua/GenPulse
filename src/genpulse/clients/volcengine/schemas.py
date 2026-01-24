from typing import Optional, List, Union, Literal, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

# --- Request Schemas ---

class VolcImageParams(BaseModel):
    """
    Parameters for VolcEngine image generation task.

    Args:
        model: Model endpoint ID.
        prompt: Description of the image.
        size: Resolution (e.g., '1K', '2048x2048').
    """
    model: str = Field(..., description="Model ID or Endpoint ID")
    prompt: str = Field(..., min_length=1, max_length=2000, description="Text prompt")
    image: Optional[Union[str, List[str]]] = Field(None, description="Input image URL(s)")
    size: str = Field("2048x2048", pattern=r"^(\d+x\d+|1K|2K|4K)$", description="Resolution")
    response_format: Literal["url", "b64_json"] = "url"
    watermark: bool = Field(False, description="Add watermark")
    sequential_image_generation: Literal["auto", "disabled"] = "disabled"
    seed: int = Field(-1, ge=-1, le=2147483647, description="Random seed")
    
    model_config = ConfigDict(extra="allow")

class VolcVideoContent(BaseModel):
    """
    Content item for video generation inputs.
    Can be text, image, or a draft task reference.
    """
    type: Literal["text", "image_url", "draft_task"] = Field(..., description="Content type")
    text: Optional[str] = Field(None, description="Prompt text")
    image_url: Optional[Dict[str, str]] = Field(None, description="{'url': '...'}")
    role: Optional[Literal["first_frame", "last_frame", "reference_image"]] = Field(None, description="Image role")
    draft_task: Optional[Dict[str, str]] = Field(None, description="Draft task ID")

class VolcVideoParams(BaseModel):
    """
    Parameters for VolcEngine video generation task.
    Supports complex multi-modal inputs via content list.
    """
    model: str = Field(..., description="Model ID or Endpoint ID")
    content: List[VolcVideoContent] = Field(..., description="List of input content items")
    resolution: Optional[Literal["480p", "720p", "1080p"]] = Field("720p", description="Output resolution")
    ratio: Optional[str] = Field("adaptive", description="Aspect ratio")
    duration: int = Field(5, description="Duration in seconds")
    generate_audio: bool = Field(True, description="Generate audio")
    seed: int = Field(-1, ge=-1, le=4294967295, description="Random seed")
    watermark: bool = Field(False, description="Add watermark")
    callback_url: Optional[str] = Field(None, description="Webhook URL")
    service_tier: Literal["default", "flex"] = Field("default", description="Service tier")
    draft: bool = Field(False, description="Enable draft mode")
    
    model_config = ConfigDict(extra="allow")

# --- Response Schemas ---

class ImageData(BaseModel):
    """Generated image data"""
    url: Optional[str] = Field(default=None, description="Image URL")
    b64_json: Optional[str] = Field(default=None, description="Image Base64")
    size: Optional[str] = Field(default=None, description="Image size")

class Usage(BaseModel):
    """
    Usage stats.
    """
    generated_images: int = Field(0, description="Count of generated images")
    output_tokens: Optional[int] = Field(0, description="Token usage")

class VideoUsage(BaseModel):
    """
    Video task usage stats.
    """
    completion_tokens: int = Field(0, description="Completion tokens used")
    total_tokens: int = Field(0, description="Total tokens used")

class ErrorInfo(BaseModel):
    """
    Error information.
    """
    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")

class ArkResponse(BaseModel):
    """
    Standard Ark response for synchronous tasks (like Image Gen).
    """
    model: str = Field(..., description="Model ID")
    created: Optional[int] = Field(None, description="Creation timestamp")
    data: Optional[List[ImageData]] = Field(None, description="Result data")
    usage: Optional[Usage] = Field(None, description="Usage statistics")
    error: Optional[ErrorInfo] = Field(None, description="Error info")

class VideoOutputContent(BaseModel):
    """
    Output content for video tasks.
    """
    video_url: Optional[str] = Field(None, description="Generated video URL")
    last_frame_url: Optional[str] = Field(None, description="Last frame image URL")

class VolcVideoStatusResponse(BaseModel):
    """
    Unified response model for Video Tasks.
    Used for both initial creation (id only) and full status query.
    """
    id: str = Field(description="Task ID")
    model: Optional[str] = Field(None, description="Model ID")
    status: Optional[Literal["queued", "running", "cancelled", "succeeded", "failed", "expired"]] = Field(None, description="Task status")
    created_at: Optional[int] = Field(None, description="Created timestamp")
    updated_at: Optional[int] = Field(None, description="Updated timestamp")
    content: Optional[VideoOutputContent] = Field(None, description="Task output")
    error: Optional[ErrorInfo] = Field(None, description="Error info")
    usage: Optional[VideoUsage] = Field(None, description="Usage stats")
    
    # Validation helpers
    @property
    def is_finished(self) -> bool:
        return self.status in ["succeeded", "failed", "cancelled", "expired"]

