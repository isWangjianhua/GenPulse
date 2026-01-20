from typing import Optional, List, Union, Literal, Dict, Any
from pydantic import BaseModel, Field

# --- Request Schemas ---

class VolcImageParams(BaseModel):
    """VolcEngine Image Generation Parameters"""
    model: str = Field(..., description="Model ID or Endpoint ID")
    prompt: str = Field(..., min_length=1, max_length=2000)
    image: Optional[Union[str, List[str]]] = None
    size: str = Field("2048x2048", pattern=r"^(\d+x\d+|1K|2K|4K)$")
    response_format: Literal["url", "b64_json"] = "url"
    watermark: bool = False
    sequential_image_generation: Literal["auto", "disabled"] = "disabled"
    seed: int = Field(-1, ge=-1, le=2147483647)
    
    class Config:
        extra = "allow"

class VolcVideoContent(BaseModel):
    """Video content item (text, image, or draft)"""
    type: Literal["text", "image_url", "draft_task"]
    text: Optional[str] = None
    image_url: Optional[Dict[str, str]] = None
    role: Optional[Literal["first_frame", "last_frame", "reference_image"]] = None
    draft_task: Optional[Dict[str, str]] = None

class VolcVideoParams(BaseModel):
    """VolcEngine Video Generation Parameters"""
    model: str = Field(..., description="Model ID or Endpoint ID")
    content: List[VolcVideoContent]
    resolution: Optional[Literal["480p", "720p", "1080p"]] = "720p"
    ratio: Optional[str] = "adaptive"
    duration: int = 5
    generate_audio: bool = True
    seed: int = Field(-1, ge=-1, le=4294967295)
    watermark: bool = False
    callback_url: Optional[str] = None
    service_tier: Literal["default", "flex"] = "default"
    draft: bool = False
    
    class Config:
        extra = "allow"

# --- Response Schemas ---

class ImageData(BaseModel):
    """Generated image data"""
    url: Optional[str] = Field(default=None, description="Image URL")
    b64_json: Optional[str] = Field(default=None, description="Image Base64")
    size: Optional[str] = Field(default=None, description="Image size")

class Usage(BaseModel):
    """Usage stats"""
    generated_images: int = 0
    output_tokens: Optional[int] = 0

class VideoUsage(BaseModel):
    """Video task usage stats"""
    completion_tokens: int = 0
    total_tokens: int = 0

class ErrorInfo(BaseModel):
    """Error information"""
    code: str
    message: str

class ArkResponse(BaseModel):
    """Standard Ark response for synchronous tasks (like Image Gen)"""
    model: str
    created: Optional[int] = None
    data: Optional[List[ImageData]] = None
    usage: Optional[Usage] = None
    error: Optional[ErrorInfo] = None

class VideoOutputContent(BaseModel):
    """Output content for video tasks"""
    video_url: Optional[str] = None
    last_frame_url: Optional[str] = None

class VolcVideoStatusResponse(BaseModel):
    """
    Unified response model for Video Tasks.
    Used for both initial creation (id only) and full status query.
    """
    id: str = Field(description="Task ID")
    model: Optional[str] = None
    status: Optional[Literal["queued", "running", "cancelled", "succeeded", "failed", "expired"]] = None
    created_at: Optional[int] = None
    updated_at: Optional[int] = None
    content: Optional[VideoOutputContent] = None
    error: Optional[ErrorInfo] = None
    usage: Optional[VideoUsage] = None
    
    # Validation helpers
    @property
    def is_finished(self) -> bool:
        return self.status in ["succeeded", "failed", "cancelled", "expired"]

