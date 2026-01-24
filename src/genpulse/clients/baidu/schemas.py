from typing import Optional, List, Literal, Any, Dict, Union
from pydantic import BaseModel, Field, ConfigDict

# --- Common Components ---

class BaiduAigcBaseInput(BaseModel):
    """
    Common parameter fields for Baidu AIGC inputs.
    """
    prompt: Optional[str] = Field(None, description="Prompt for generation")
    negativePrompt: Optional[str] = Field(None, description="Negative prompt")
    duration: Optional[int] = Field(5, description="Duration in seconds (5, 10, 15)")
    resolution: Optional[str] = Field("720p", description="Resolution (e.g., '1080p')")
    aspectRatio: Optional[str] = Field("16:9", description="Aspect ratio")
    watermark: bool = Field(False, description="Add watermark")

    model_config = ConfigDict(extra="allow")

class BaiduAigcImageInput(BaiduAigcBaseInput):
    """
    Input fields specific to Image-to-Video tasks.
    """
    image: str = Field(..., description="Source image URL or Base64")
    imageTail: Optional[str] = Field(None, description="Optional ending frame image")

# --- Request Schemas ---

class BaiduTextToVideoParams(BaseModel):
    """
    Parameters for Baidu Text-to-Video generation.
    """
    model: str = Field(..., description="Model ID (e.g., 'K25T', 'V15')")
    taskInput: BaiduAigcBaseInput = Field(..., description="Task input parameters")

class BaiduImageToVideoParams(BaseModel):
    """
    Parameters for Baidu Image-to-Video generation.
    """
    model: str = Field(..., description="Model ID (e.g., 'K25T', 'K21M')")
    taskInput: BaiduAigcImageInput = Field(..., description="Task input parameters")

# --- Extension and Lip-sync Schemas ---

class BaiduVideoExtendInput(BaiduAigcBaseInput):
    """
    Input fields for video extension tasks.
    """
    mediaId: Optional[str] = Field(None, description="Source video MediaId")
    videoUrl: Optional[str] = Field(None, description="Source video URL")
    extendDuration: Optional[int] = Field(5, description="Extension duration in seconds")
    # For VQ2T/VQ2P
    tailImage: Optional[str] = Field(None, description="New ending frame")

class BaiduVideoExtendParams(BaseModel):
    """
    Parameters for video extension tasks.
    """
    model: str = Field(..., description="Model ID (e.g., 'P35', 'K', 'VQ2T')")
    taskInput: BaiduVideoExtendInput

class BaiduLipSyncInput(BaseModel):
    """
    Input fields for lip-sync tasks.
    """
    mediaId: Optional[str] = Field(None, description="Video MediaId")
    videoUrl: Optional[str] = Field(None, description="Video URL")
    audioId: Optional[str] = Field(None, description="Audio MediaId")
    audioUrl: Optional[str] = Field(None, description="Audio URL")

class BaiduLipSyncParams(BaseModel):
    """
    Parameters for lip-sync tasks.
    """
    model: Literal["K", "P"] = Field(..., description="Model identifier")
    taskInput: BaiduLipSyncInput

# --- Image Generation Schemas ---

class BaiduImageInput(BaiduAigcBaseInput):
    """
    Fields for image generation tasks.
    """
    n: Optional[int] = Field(1, description="Number of images to generate")
    sampler: Optional[str] = Field(None, description="Sampling method (e.g., 'Euler a')")
    steps: Optional[int] = Field(None, description="Inference steps")
    seed: Optional[int] = Field(None, description="Random seed")
    style: Optional[str] = Field(None, description="Image style preset")
    # For image-to-image
    image: Optional[str] = Field(None, description="Source image (URL or Base64)")
    strength: Optional[float] = Field(0.75, description="Denoising strength")

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
    """
    Fields for video-to-video generation.
    """
    mediaId: Optional[str] = Field(None, description="Source video MediaId")
    videoUrl: Optional[str] = Field(None, description="Source video URL")
    # For some models, video to video might involve specific style or prompt
    strength: Optional[float] = Field(0.5, description="Style strength") 

class BaiduVideoToVideoParams(BaseModel):
    """
    Parameters for Baidu Video-to-Video generation.
    """
    model: str = Field(..., description="Model ID (e.g., 'VQ2T', 'K', etc.)")
    taskInput: BaiduVideoToVideoInput = Field(..., description="Task input parameters")

# --- Response Schemas ---

class BaiduAigcResponse(BaseModel):
    """
    Initial response from task creation.
    """
    taskId: str = Field(..., description="The created Task ID")
    requestId: Optional[str] = Field(None, description="Request ID for tracking")

class BaiduAigcResult(BaseModel):
    """
    Result details in status response for both video and image.
    """
    videoUrl: Optional[str] = Field(None, description="Generated video URL")
    imageUrls: Optional[List[str]] = Field(None, description="List of generated image URLs")
    coverUrl: Optional[str] = Field(None, description="Video cover image URL")
    duration: Optional[float] = Field(None, description="Actual duration of the video")
    size: Optional[int] = Field(None, description="File size in bytes")

class BaiduStatusResponse(BaseModel):
    """
    Status query response.
    """
    taskId: str = Field(..., description="Task ID")
    status: Literal["PROCESSING", "SUCCESS", "FAILED"] = Field(..., description="Current task status")
    result: Optional[BaiduAigcResult] = Field(None, description="Result data if success")
    error: Optional[Dict[str, Any]] = Field(None, description="Error details if failed")
    
    @property
    def is_finished(self) -> bool:
        return self.status in ["SUCCESS", "FAILED"]

    @property
    def is_succeeded(self) -> bool:
        return self.status == "SUCCESS"

class BaiduTaskListParams(BaseModel):
    """
    Parameters for querying task list.
    """
    pn: Optional[int] = Field(1, description="Page number")
    ps: Optional[int] = Field(20, description="Page size")

class BaiduTaskListResponse(BaseModel):
    """
    Response when querying task list.
    """
    tasks: List[BaiduStatusResponse] = Field(..., description="List of tasks")
    totalCount: int = Field(..., description="Total number of tasks")
    pn: int = Field(..., description="Current page number")
    ps: int = Field(..., description="Current page size")

