from typing import Literal, Union, Optional
from typing_extensions import Annotated
from pydantic import BaseModel, Field

from .params import (
    # Video params
    VolcVideoParams,
    KlingTextToVideoParams,
    KlingImageToVideoParams,
    MinimaxTextToVideoParams,
    MinimaxImageToVideoParams,
    DashScopeVideoParams,
    BaiduTextToVideoParams,
    BaiduImageToVideoParams,
    TencentVideoParams,
    # Image params
    VolcImageParams,
    MinimaxImageParams,
    DashScopeImageParams,
    BaiduImageParams,
    TencentImageParams,
    # Special
    ComfyParams,
    MockParams,
)


# ============================================================================
# Base Request
# ============================================================================

class BaseRequest(BaseModel):
    """Base request with common fields."""
    priority: str = Field("normal", description="Execution priority: 'high', 'normal', 'low'.")
    callback_url: Optional[str] = Field(None, description="Webhook URL to call when task completes.")


# ============================================================================
# Text-to-Video Request
# ============================================================================

TextToVideoParams = Annotated[
    Union[
        VolcVideoParams,
        KlingTextToVideoParams,
        MinimaxTextToVideoParams,
        DashScopeVideoParams,
        BaiduTextToVideoParams,
        TencentVideoParams,
        MockParams,
    ],
    Field(discriminator="provider")
]

class TextToVideoRequest(BaseRequest):
    """Request for Text-to-Video generation."""
    task_type: Literal["text-to-video"] = "text-to-video"
    params: TextToVideoParams


# ============================================================================
# Image-to-Video Request
# ============================================================================

ImageToVideoParams = Annotated[
    Union[
        VolcVideoParams,  # Volc uses same schema for T2V and I2V (via content field)
        KlingImageToVideoParams,
        MinimaxImageToVideoParams,
        DashScopeVideoParams,  # DashScope I2V uses first_frame_url
        BaiduImageToVideoParams,
        TencentVideoParams,  # Tencent uses FileInfos for I2V
        MockParams,
    ],
    Field(discriminator="provider")
]

class ImageToVideoRequest(BaseRequest):
    """Request for Image-to-Video generation."""
    task_type: Literal["image-to-video"] = "image-to-video"
    params: ImageToVideoParams


# ============================================================================
# Text-to-Image Request
# ============================================================================

TextToImageParams = Annotated[
    Union[
        VolcImageParams,
        MinimaxImageParams,
        DashScopeImageParams,
        BaiduImageParams,
        TencentImageParams,
        MockParams,
    ],
    Field(discriminator="provider")
]

class TextToImageRequest(BaseRequest):
    """Request for Text-to-Image generation."""
    task_type: Literal["text-to-image"] = "text-to-image"
    params: TextToImageParams


# ============================================================================
# Image-to-Image Request
# ============================================================================

ImageToImageParams = Annotated[
    Union[
        VolcImageParams,  # Volc uses 'image' field for I2I
        BaiduImageParams,  # Baidu I2I uses 'image' + 'strength'
        MockParams,
    ],
    Field(discriminator="provider")
]

class ImageToImageRequest(BaseRequest):
    """Request for Image-to-Image generation."""
    task_type: Literal["image-to-image"] = "image-to-image"
    params: ImageToImageParams


# ============================================================================
# ComfyUI Workflow Request
# ============================================================================

class ComfyWorkflowRequest(BaseRequest):
    """Request for direct ComfyUI workflow execution."""
    task_type: Literal["comfy-workflow"] = "comfy-workflow"
    params: ComfyParams


# ============================================================================
# Unified Task Request (discriminated union by task_type)
# ============================================================================

TaskRequest = Annotated[
    Union[
        TextToVideoRequest,
        ImageToVideoRequest,
        TextToImageRequest,
        ImageToImageRequest,
        ComfyWorkflowRequest,
    ],
    Field(discriminator="task_type")
]
