from typing import Optional, List, Literal, Any, Dict, Union
from pydantic import BaseModel, Field

# --- Common Components ---

class BaiduAigcBaseInput(BaseModel):
    """Common fields for Baidu AIGC inputs"""
    prompt: Optional[str] = Field(None, description="Prompt for generation")
    negativePrompt: Optional[str] = None
    duration: Optional[int] = 5
    resolution: Optional[str] = "720p"
    aspectRatio: Optional[str] = "16:9"
    watermark: bool = False

class BaiduAigcImageInput(BaiduAigcBaseInput):
    """Fields for image-to-video"""
    image: str = Field(..., description="Source image URL or Base64")
    imageTail: Optional[str] = None

# --- Request Schemas ---

class BaiduTextToVideoParams(BaseModel):
    """Request schema for text-to-video"""
    model: str = Field(..., description="Model ID (e.g., K25T, V15)")
    # Since Baidu uses dynamic keys like modelK25TTaskInput, 
    # we'll use a flexible approach or a dictionary.
    taskInput: BaiduAigcBaseInput

class BaiduImageToVideoParams(BaseModel):
    """Request schema for image-to-video"""
    model: str = Field(..., description="Model ID (e.g., K25T, K21M)")
    taskInput: BaiduAigcImageInput

# --- Extension and Lip-sync Schemas ---

class BaiduVideoExtendInput(BaiduAigcBaseInput):
    """Fields for video extension"""
    mediaId: Optional[str] = None
    videoUrl: Optional[str] = None
    extendDuration: Optional[int] = 5
    # For VQ2T/VQ2P
    tailImage: Optional[str] = None

class BaiduVideoExtendParams(BaseModel):
    """Request schema for video-extend"""
    model: str = Field(..., description="Model ID (e.g., P35, K, VQ2T)")
    taskInput: BaiduVideoExtendInput

class BaiduLipSyncInput(BaseModel):
    """Fields for lip-sync task"""
    mediaId: Optional[str] = None
    videoUrl: Optional[str] = None
    audioId: Optional[str] = None
    audioUrl: Optional[str] = None

class BaiduLipSyncParams(BaseModel):
    """Request schema for lip-sync"""
    model: Literal["K", "P"]
    taskInput: BaiduLipSyncInput

# --- Image Generation Schemas ---

class BaiduImageInput(BaiduAigcBaseInput):
    """Fields for image generation tasks"""
    n: Optional[int] = 1
    sampler: Optional[str] = None
    steps: Optional[int] = None
    seed: Optional[int] = None
    style: Optional[str] = None
    # For image-to-image
    image: Optional[str] = None
    strength: Optional[float] = 0.75

class BaiduTextToImageParams(BaseModel):
    """Request schema for text-to-image"""
    model: str = Field(..., description="Model ID (e.g., SDXL, FLUX)")
    taskInput: BaiduImageInput

class BaiduImageToImageParams(BaseModel):
    """Request schema for image-to-image"""
    model: str = Field(..., description="Model ID (e.g., SDXL, FLUX)")
    taskInput: BaiduImageInput

class BaiduLargeModelImageParams(BaseModel):
    """Request schema for large model image generation"""
    model: str = Field(..., description="Model ID (e.g., ERNIE-ViLG)")
    taskInput: BaiduImageInput

# --- Video-to-Video Schemas ---

class BaiduVideoToVideoInput(BaiduAigcBaseInput):
    """Fields for video-to-video generation"""
    mediaId: Optional[str] = None
    videoUrl: Optional[str] = None
    # For some models, video to video might involve specific style or prompt
    strength: Optional[float] = 0.5 

class BaiduVideoToVideoParams(BaseModel):
    """Request schema for video-to-video"""
    model: str = Field(..., description="Model ID (e.g., VQ2T, K, etc.)")
    taskInput: BaiduVideoToVideoInput

# --- Response Schemas ---

class BaiduAigcResponse(BaseModel):
    """Initial response from task creation"""
    taskId: str
    requestId: Optional[str] = None

class BaiduAigcResult(BaseModel):
    """Result details in status response for both video and image"""
    videoUrl: Optional[str] = None
    imageUrls: Optional[List[str]] = None
    coverUrl: Optional[str] = None
    duration: Optional[float] = None
    size: Optional[int] = None

class BaiduStatusResponse(BaseModel):
    """Status query response"""
    taskId: str
    status: Literal["PROCESSING", "SUCCESS", "FAILED"]
    result: Optional[BaiduAigcResult] = None
    error: Optional[Dict[str, Any]] = None
    
    @property
    def is_finished(self) -> bool:
        return self.status in ["SUCCESS", "FAILED"]

    @property
    def is_succeeded(self) -> bool:
        return self.status == "SUCCESS"

class BaiduTaskListParams(BaseModel):
    """Parameters for querying task list"""
    pn: Optional[int] = 1
    ps: Optional[int] = 20

class BaiduTaskListResponse(BaseModel):
    """Response when querying task list"""
    tasks: List[BaiduStatusResponse]
    totalCount: int
    pn: int
    ps: int

