from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any, Literal, Union

# ============================================================================
# Base Model
# ============================================================================

class BaseParams(BaseModel):
    """Base class with common configuration."""
    model_config = ConfigDict(extra="allow")


# ============================================================================
# VolcEngine Parameters
# ============================================================================

class VolcImageParams(BaseParams):
    """Parameters for VolcEngine Image Generation (T2I, I2I)."""
    provider: Literal["volcengine"] = "volcengine"
    model: str = Field(..., description="Model ID or Endpoint ID")
    prompt: str = Field(..., min_length=1, max_length=2000, description="Text prompt")
    image: Optional[Union[str, List[str]]] = Field(None, description="Input image URL(s) for I2I")
    size: str = Field("2048x2048", description="Resolution (e.g., '2048x2048', '1K', '2K')")
    response_format: Literal["url", "b64_json"] = "url"
    watermark: bool = Field(False, description="Add watermark")
    sequential_image_generation: Literal["auto", "disabled"] = "disabled"
    seed: int = Field(-1, ge=-1, le=2147483647, description="Random seed")

class VolcVideoParams(BaseParams):
    """Parameters for VolcEngine Video Generation (T2V, I2V)."""
    provider: Literal["volcengine"] = "volcengine"
    model: str = Field(..., description="Model ID or Endpoint ID")
    content: List[Dict[str, Any]] = Field(..., description="List of input content items (text/image)")
    resolution: Optional[Literal["480p", "720p", "1080p"]] = Field("720p", description="Output resolution")
    ratio: Optional[str] = Field("adaptive", description="Aspect ratio")
    duration: int = Field(5, description="Duration in seconds")
    generate_audio: bool = Field(True, description="Generate audio")
    seed: int = Field(-1, ge=-1, le=4294967295, description="Random seed")
    watermark: bool = Field(False, description="Add watermark")
    callback_url: Optional[str] = Field(None, description="Webhook URL")
    service_tier: Literal["default", "flex"] = Field("default", description="Service tier")
    draft: bool = Field(False, description="Enable draft mode")


# ============================================================================
# Kling Parameters
# ============================================================================

class KlingTextToVideoParams(BaseParams):
    """Parameters for Kling Text-to-Video."""
    provider: Literal["kling"] = "kling"
    model_name: str = Field("kling-v1", description="Model name")
    prompt: str = Field(..., max_length=2500, description="Detailed text prompt")
    negative_prompt: Optional[str] = Field(None, max_length=2500, description="Negative prompt")
    sound: Literal["on", "off"] = Field("off", description="Generate sound")
    cfg_scale: float = Field(0.5, ge=0.0, le=1.0, description="Guidance scale")
    mode: Literal["std", "pro"] = Field("std", description="Performance mode")
    aspect_ratio: Literal["16:9", "9:16", "1:1"] = Field("16:9", description="Video aspect ratio")
    duration: Literal["5", "10"] = Field("5", description="Duration in seconds")
    callback_url: Optional[str] = None
    external_task_id: Optional[str] = None
    camera_control: Optional[Dict[str, Any]] = Field(None, description="Camera movement settings")

class KlingImageToVideoParams(BaseParams):
    """Parameters for Kling Image-to-Video."""
    provider: Literal["kling"] = "kling"
    model_name: str = Field("kling-v1", description="Model name")
    prompt: str = Field(..., max_length=2500, description="Description of the motion/content")
    image: str = Field(..., description="The starting frame image (URL or Base64)")
    image_tail: Optional[str] = Field(None, description="The ending frame image for transition")
    negative_prompt: Optional[str] = Field(None, max_length=2500)
    sound: Literal["on", "off"] = Field("off")
    cfg_scale: float = Field(0.5, ge=0.0, le=1.0)
    mode: Literal["std", "pro"] = Field("std")
    aspect_ratio: Literal["16:9", "9:16", "1:1"] = Field("16:9")
    duration: Literal["5", "10"] = Field("5")
    callback_url: Optional[str] = None
    external_task_id: Optional[str] = None


# ============================================================================
# Minimax Parameters
# ============================================================================

class MinimaxTextToVideoParams(BaseParams):
    """Parameters for MiniMax Text-to-Video."""
    provider: Literal["minimax"] = "minimax"
    model: str = Field(..., description="Model ID (e.g., 'MiniMax-Hailuo-2.3')")
    prompt: str = Field(..., max_length=2000, description="Prompt text")
    prompt_optimizer: bool = Field(True, description="Optimize prompt")
    fast_pretreatment: bool = False
    duration: Optional[int] = Field(6, description="Duration in seconds")
    resolution: Optional[Literal["512P", "720P", "768P", "1080P"]] = "768P"
    callback_url: Optional[str] = None
    aigc_watermark: bool = False

class MinimaxImageToVideoParams(BaseParams):
    """Parameters for MiniMax Image-to-Video."""
    provider: Literal["minimax"] = "minimax"
    model: str = Field(..., description="Model ID")
    prompt: str = Field(..., max_length=2000, description="Prompt text")
    first_frame_image: Optional[str] = Field(None, description="Start frame image")
    last_frame_image: Optional[str] = Field(None, description="End frame image")
    subject_reference: Optional[List[Dict[str, Any]]] = Field(None, description="Character consistency ref")
    prompt_optimizer: bool = Field(True)
    fast_pretreatment: bool = False
    duration: Optional[int] = Field(6)
    resolution: Optional[Literal["512P", "720P", "768P", "1080P"]] = "768P"
    callback_url: Optional[str] = None
    aigc_watermark: bool = False

class MinimaxImageParams(BaseParams):
    """Parameters for MiniMax Image Generation."""
    provider: Literal["minimax"] = "minimax"
    model: Literal["image-01", "image-01-live"] = Field("image-01", description="Model ID")
    prompt: str = Field(..., max_length=1500, description="Image prompt")
    style: Optional[Dict[str, Any]] = Field(None, description="Style settings (image-01-live only)")
    subject_reference: Optional[List[Dict[str, Any]]] = None
    aspect_ratio: Optional[Literal["1:1", "16:9", "4:3", "3:2", "2:3", "3:4", "9:16", "21:9"]] = "1:1"
    width: Optional[int] = None
    height: Optional[int] = None
    response_format: Literal["url", "base64"] = "url"
    seed: Optional[int] = None
    n: int = Field(1, ge=1, le=9, description="Number of images")
    prompt_optimizer: bool = False
    aigc_watermark: bool = False


# ============================================================================
# DashScope Parameters
# ============================================================================

class DashScopeImageParams(BaseParams):
    """Parameters for DashScope Image Generation."""
    provider: Literal["dashscope"] = "dashscope"
    model: str = Field(..., description="Model ID (e.g., 'qwen-image-plus')")
    prompt: str = Field(..., min_length=1, max_length=500, description="Text prompt")
    negative_prompt: Optional[str] = Field(" ", description="Negative prompt")
    n: int = Field(1, ge=1, le=4, description="Number of images")
    size: str = Field("1024*1024", description="Image resolution")
    seed: Optional[int] = Field(None, ge=0, le=4294967290)
    style: Optional[str] = Field("<auto>", description="Image style")
    prompt_extend: bool = Field(True, description="Enable prompt enhancement")
    watermark: bool = False

class DashScopeVideoParams(BaseParams):
    """Parameters for DashScope Video Generation (T2V, I2V)."""
    provider: Literal["dashscope"] = "dashscope"
    model: str = Field(..., description="Model ID (e.g., 'wan2.5-t2v-preview')")
    prompt: str = Field(..., min_length=1, description="Video description")
    resolution: Optional[Literal["480P", "720P", "1080P"]] = None
    size: Optional[str] = Field(None, description="Resolution e.g. '832*480'")
    duration: Optional[int] = Field(None, description="Duration in seconds")
    audio_url: Optional[str] = Field(None, description="Audio file URL to sync")
    negative_prompt: Optional[str] = None
    seed: Optional[int] = None
    first_frame_url: Optional[str] = Field(None, description="Start frame for I2V")
    last_frame_url: Optional[str] = Field(None, description="End frame for I2V")
    prompt_extend: bool = True
    watermark: bool = False


# ============================================================================
# Baidu Parameters
# ============================================================================

class BaiduTextToVideoParams(BaseParams):
    """Parameters for Baidu Text-to-Video."""
    provider: Literal["baidu"] = "baidu"
    model: str = Field(..., description="Model ID (e.g., 'univid-v2')")
    prompt: str = Field(..., description="Prompt for generation")
    negative_prompt: Optional[str] = None
    duration: Optional[int] = Field(5, description="Duration in seconds (5, 10, 15)")
    resolution: Optional[str] = Field("720p", description="Resolution (e.g., '1080p')")
    aspect_ratio: Optional[str] = Field("16:9", description="Aspect ratio")
    watermark: bool = False

class BaiduImageToVideoParams(BaseParams):
    """Parameters for Baidu Image-to-Video."""
    provider: Literal["baidu"] = "baidu"
    model: str = Field(..., description="Model ID")
    prompt: Optional[str] = None
    image: str = Field(..., description="Source image URL or Base64")
    image_tail: Optional[str] = Field(None, description="Optional ending frame image")
    negative_prompt: Optional[str] = None
    duration: Optional[int] = Field(5)
    resolution: Optional[str] = Field("720p")
    aspect_ratio: Optional[str] = Field("16:9")
    watermark: bool = False

class BaiduImageParams(BaseParams):
    """Parameters for Baidu Image Generation (T2I, I2I)."""
    provider: Literal["baidu"] = "baidu"
    model: str = Field(..., description="Model ID (e.g., 'Stable-Diffusion-XL')")
    prompt: str = Field(..., description="Prompt for generation")
    negative_prompt: Optional[str] = None
    resolution: Optional[str] = Field(None, description="Resolution (e.g., '1024x1024')")
    aspect_ratio: Optional[str] = None
    style: Optional[str] = None
    n: Optional[int] = Field(1, description="Number of images")
    sampler: Optional[str] = Field(None, description="Sampling method (e.g., 'Euler a')")
    steps: Optional[int] = None
    seed: Optional[int] = None
    # For I2I
    image: Optional[str] = Field(None, description="Input image URL or Base64")
    strength: Optional[float] = Field(0.75, description="Denoising strength")
    watermark: bool = False


# ============================================================================
# Tencent Parameters
# ============================================================================

class TencentVideoParams(BaseParams):
    """Parameters for Tencent Video Generation (T2V, I2V)."""
    provider: Literal["tencent"] = "tencent"
    model_name: Literal["Hailuo", "Kling", "Jimeng", "Vidu", "Hunyuan", "Mingmou", "GV", "OS"] = Field(..., description="Model name")
    model_version: str = Field(..., description="Model version")
    prompt: Optional[str] = Field(None, description="Prompt for video generation")
    negative_prompt: Optional[str] = None
    
    # Input assets
    file_infos: Optional[List[Dict[str, Any]]] = Field(None, description="List of input assets (max 3)")
    last_frame_file_id: Optional[str] = None
    last_frame_url: Optional[str] = None
    
    # Output configuration
    sub_app_id: Optional[int] = None
    storage_mode: Literal["Permanent", "Temporary"] = "Temporary"
    media_name: Optional[str] = None
    class_id: Optional[int] = 0
    expire_time: Optional[str] = None
    resolution: Optional[str] = None
    aspect_ratio: Optional[str] = None
    audio_generation: Optional[Literal["Enabled", "Disabled"]] = "Disabled"
    person_generation: Optional[Literal["AllowAdult", "Disallowed"]] = None
    input_compliance_check: Optional[Literal["Enabled", "Disabled"]] = "Enabled"
    output_compliance_check: Optional[Literal["Enabled", "Disabled"]] = "Enabled"
    enhance_switch: Optional[Literal["Enabled", "Disabled"]] = None
    
    # Optimization
    enhance_prompt: Optional[Literal["Enabled", "Disabled"]] = "Disabled"
    input_region: Optional[Literal["Oversea", "Mainland"]] = "Mainland"
    scene_type: Optional[str] = None
    session_id: Optional[str] = None
    session_context: Optional[str] = None
    tasks_priority: Optional[int] = 0
    ext_info: Optional[str] = None

class TencentImageParams(BaseParams):
    """Parameters for Tencent Image Generation."""
    provider: Literal["tencent"] = "tencent"
    model_name: Literal["GEM", "Qwen", "Hunyuan"] = Field("Hunyuan", description="Model name")
    model_version: str = Field("3.0", description="Model version")
    prompt: Optional[str] = Field(None, description="Prompt for image generation")
    negative_prompt: Optional[str] = None
    
    # Input
    file_infos: Optional[List[Dict[str, Any]]] = None
    
    # Output configuration
    sub_app_id: Optional[int] = None
    storage_mode: Literal["Permanent", "Temporary"] = "Temporary"
    media_name: Optional[str] = None
    resolution: Optional[str] = None
    aspect_ratio: Optional[str] = None
    person_generation: Optional[Literal["AllowAdult", "Disallowed"]] = None
    input_compliance_check: Optional[Literal["Enabled", "Disabled"]] = "Enabled"
    output_compliance_check: Optional[Literal["Enabled", "Disabled"]] = "Enabled"
    
    # Optimization
    enhance_prompt: Optional[Literal["Enabled", "Disabled"]] = "Disabled"
    session_id: Optional[str] = None
    session_context: Optional[str] = None
    tasks_priority: Optional[int] = 0
    ext_info: Optional[str] = None


# ============================================================================
# ComfyUI and Mock
# ============================================================================

class ComfyParams(BaseModel):
    """Direct ComfyUI execution."""
    provider: Literal["comfyui"] = "comfyui"
    workflow: Dict[str, Any] = Field(..., description="The ComfyUI API JSON structure")
    inputs: Dict[str, Any] = Field(default_factory=dict, description="Variables to inject")
    server_address: Optional[str] = None

class MockParams(BaseModel):
    """Mock provider for testing."""
    provider: Literal["mock"] = "mock"
    model: str = "mock-v1"
    prompt: Optional[str] = None
    duration: int = 5
