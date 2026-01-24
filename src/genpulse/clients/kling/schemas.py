from typing import Optional, Literal, Dict, Any, Union, List
from pydantic import BaseModel, Field, ConfigDict

# --- Base and Common Components ---

class KlingCameraConfig(BaseModel):
    """
    Detailed configuration for camera path control.
    """
    horizontal: float = Field(0.0, description="Horizontal movement (-10 to 10)")
    vertical: float = Field(0.0, description="Vertical movement (-10 to 10)")
    pan: float = Field(0.0, description="Pan rotation (-10 to 10)")
    tilt: float = Field(0.0, description="Tilt rotation (-10 to 10)")
    roll: float = Field(0.0, description="Roll rotation (-10 to 10)")
    zoom: float = Field(0.0, description="Zoom level (-10 to 10)")

class KlingCameraControl(BaseModel):
    """
    Camera control wrapper.
    Accepts predefined types or custom configuration.
    """
    type: Literal["simple", "down_back", "forward_up", "right_turn_forward", "left_turn_forward"] = Field(..., description="Movement type")
    config: Optional[KlingCameraConfig] = Field(None, description="Custom config for 'simple' type")

class KlingImageItem(BaseModel):
    """Wrapped image reference."""
    image: str = Field(..., description="URL or Base64 string of the image")

class KlingBaseParams(BaseModel):
    """
    Common parameters for all Kling video generation tasks.

    Args:
        model_name: Model identifier (e.g., 'kling-v1').
        mode: Generation mode ('std' for standard, 'pro' for professional).
        duration: Video duration in seconds ('5' or '10').
    """
    model_name: str = Field(default="kling-v1", description="Model name")
    prompt: Optional[str] = Field(None, max_length=2500, description="Video description")
    negative_prompt: Optional[str] = Field(default=None, max_length=2500, description="Negative prompt")
    sound: Literal["on", "off"] = Field("off", description="Generate sound")
    cfg_scale: float = Field(default=0.5, ge=0.0, le=1.0, description="Guidance scale")
    mode: Literal["std", "pro"] = Field("std", description="Performance mode")
    aspect_ratio: Literal["16:9", "9:16", "1:1"] = Field("16:9", description="Video aspect ratio")
    duration: Literal["5", "10"] = Field("5", description="Duration in seconds")
    callback_url: Optional[str] = Field(None, description="Webhook URL")
    external_task_id: Optional[str] = Field(None, description="Client-side task tracking ID")

    model_config = ConfigDict(extra="allow")

# --- Specific Input Schemas ---

class KlingTextToVideoParams(KlingBaseParams):
    """
    Parameters for pure Text-to-Video generation.
    """
    prompt: str = Field(..., max_length=2500, description="Detailed text prompt")
    camera_control: Optional[KlingCameraControl] = Field(None, description="Camera movement settings")

class KlingImageToVideoParams(KlingBaseParams):
    """
    Parameters for Image-to-Video generation.
    """
    prompt: str = Field(..., max_length=2500, description="Description of the motion/content")
    image: str = Field(..., description="The starting frame image (URL or Base64)")
    image_tail: Optional[str] = Field(None, description="The ending frame image for transition")

class KlingMultiImageToVideoParams(KlingBaseParams):
    """
    Parameters for Multi-image reference video generation.
    """
    prompt: str = Field(..., max_length=2500, description="Description of the video (optional)")
    image_list: List[KlingImageItem] = Field(..., min_items=1, max_items=4, description="Reference images (max 4)")

# --- Response Schemas ---

class KlingTaskInfo(BaseModel):
    """Task metadata."""
    external_task_id: Optional[str] = Field(None, description="Client-side task ID")

class KlingVideoInfo(BaseModel):
    """Generated video metadata."""
    video_url: Optional[str] = Field(None, description="Download URL for the video")

class KlingTaskData(BaseModel):
    """Inner data object for task status."""
    task_id: str = Field(..., description="Kling Task ID")
    task_status: str = Field(..., description="Status (submitted, processing, succeed, failed)") 
    task_info: Optional[KlingTaskInfo] = Field(None, description="Task info")
    video_info: Optional[KlingVideoInfo] = Field(None, description="Video result info")
    created_at: int = Field(..., description="Creation timestamp (ms)")
    updated_at: int = Field(..., description="Last update timestamp (ms)")

class KlingStatusResponse(BaseModel):
    """
    Standard Kling API response format.
    """
    code: int = Field(..., description="Error code (0 for success)")
    message: str = Field(..., description="Error message")
    request_id: str = Field(..., description="Request trace ID")
    data: KlingTaskData = Field(..., description="Response payload")

    @property
    def is_finished(self) -> bool:
        return self.data.task_status in ["succeed", "failed"]

    @property
    def is_succeeded(self) -> bool:
        return self.data.task_status == "succeed"

