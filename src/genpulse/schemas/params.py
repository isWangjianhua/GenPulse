from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class BaseParams(BaseModel):
    prompt: str = Field(..., description="Main positive prompt describing the desired output.")
    extra: Dict[str, Any] = Field(default_factory=dict, description="Escape hatch for provider-specific parameters not covered here.")
    
    class Config:
        extra = "allow"

class VolcParams(BaseParams):
    model: str = Field("video-1.0", description="VolcEngine model identifier.")
    negative_prompt: Optional[str] = None
    width: int = Field(1280, description="Video width.")
    height: int = Field(720, description="Video height.")
    fps: int = Field(24, description="Frames per second.")

class KlingParams(BaseParams):
    model: str = Field("kling-v1", description="Kling model identifier.")
    negative_prompt: Optional[str] = None
    aspect_ratio: str = Field("16:9", description="Desired aspect ratio (e.g. 16:9, 1:1).")
    duration: int = Field(5, description="Video duration in seconds (5 or 10).")
    mode: str = Field("std", description="Generation mode: 'std' or 'pro'.")

class MinimaxParams(BaseParams):
    model: str = Field("video-01", description="Minimax model identifier.")
    first_frame_image: Optional[str] = Field(None, description="URL of the image to use as the first frame (Image-to-Video).")

class DashScopeParams(BaseParams):
    model: str = Field("wanx-v1", description="DashScope model identifier.")
    size: str = Field("1024*1024", description="Resolution string.")

class MockParams(BaseParams):
    model: str = "mock-v1"
    duration: int = 5
