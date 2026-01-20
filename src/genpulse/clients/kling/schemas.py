from typing import Optional, Literal, Dict, Any, Union, List
from pydantic import BaseModel, Field

# --- Base and Common Components ---

class KlingCameraConfig(BaseModel):
    """Configuration for simple camera movements"""
    horizontal: float = 0.0
    vertical: float = 0.0
    pan: float = 0.0
    tilt: float = 0.0
    roll: float = 0.0
    zoom: float = 0.0

class KlingCameraControl(BaseModel):
    """Camera movement control protocols"""
    type: Literal["simple", "down_back", "forward_up", "right_turn_forward", "left_turn_forward"]
    config: Optional[KlingCameraConfig] = None

class KlingImageItem(BaseModel):
    """Image item for multi-image requests"""
    image: str = Field(..., description="URL or Base64 of the image")

class KlingBaseParams(BaseModel):
    """Base parameters shared across all video models"""
    model_name: str = Field(default="kling-v1", description="Model name")
    prompt: Optional[str] = Field(None, max_length=2500)
    negative_prompt: Optional[str] = Field(default=None, max_length=2500)
    sound: Literal["on", "off"] = "off"
    cfg_scale: float = Field(default=0.5, ge=0.0, le=1.0)
    mode: Literal["std", "pro"] = "std"
    aspect_ratio: Literal["16:9", "9:16", "1:1"] = "16:9"
    duration: Literal["5", "10"] = "5"
    callback_url: Optional[str] = None
    external_task_id: Optional[str] = None

    class Config:
        extra = "allow"

# --- Specific Input Schemas ---

class KlingTextToVideoParams(KlingBaseParams):
    """Parameters for pure Text-to-Video generation"""
    prompt: str = Field(..., max_length=2500)
    camera_control: Optional[KlingCameraControl] = None

class KlingImageToVideoParams(KlingBaseParams):
    """Parameters for Image-to-Video generation"""
    prompt: str = Field(..., max_length=2500)
    image: str = Field(..., description="The starting frame image (URL or Base64)")
    image_tail: Optional[str] = Field(None, description="The ending frame image for transition")

class KlingMultiImageToVideoParams(KlingBaseParams):
    """Parameters for Multi-image reference video generation"""
    prompt: str = Field(..., max_length=2500)
    image_list: List[KlingImageItem] = Field(..., min_items=1, max_items=4, description="Reference images (max 4)")

# --- Response Schemas ---

class KlingTaskInfo(BaseModel):
    external_task_id: Optional[str] = None

class KlingVideoInfo(BaseModel):
    video_url: Optional[str] = None

class KlingTaskData(BaseModel):
    task_id: str
    task_status: str # submitted, processing, succeed, failed
    task_info: Optional[KlingTaskInfo] = None
    video_info: Optional[KlingVideoInfo] = None
    created_at: int
    updated_at: int

class KlingStatusResponse(BaseModel):
    """Standard Kling API response format"""
    code: int
    message: str
    request_id: str
    data: KlingTaskData

    @property
    def is_finished(self) -> bool:
        return self.data.task_status in ["succeed", "failed"]

    @property
    def is_succeeded(self) -> bool:
        return self.data.task_status == "succeed"

