from typing import Literal, Union, Optional
from typing_extensions import Annotated
from pydantic import BaseModel, Field
from .params import VolcParams, KlingParams, MinimaxParams, DashScopeParams, MockParams

class BaseRequest(BaseModel):
    task_type: str = Field(..., description="Type of task to execute (e.g., 'text-to-video', 'image-to-video').")
    priority: str = Field("normal", description="Execution priority: 'high', 'normal', 'low'.")
    callback_url: Optional[str] = Field(None, description="Webhook URL to call when task completes.")

# --- Specific Requests ---

class VolcRequest(BaseRequest):
    provider: Literal["volcengine"] = Field(description="Use VolcEngine provider.")
    params: VolcParams

class KlingRequest(BaseRequest):
    provider: Literal["kling"] = Field(description="Use Kling AI provider.")
    params: KlingParams

class MinimaxRequest(BaseRequest):
    provider: Literal["minimax"] = Field(description="Use Minimax provider.")
    params: MinimaxParams

class DashScopeRequest(BaseRequest):
    provider: Literal["dashscope"] = Field(description="Use DashScope (Alibaba) provider.")
    params: DashScopeParams

class MockRequest(BaseRequest):
    provider: Literal["mock"] = Field(description="Use Mock provider for testing.")
    params: MockParams

# --- Union Type ---

TaskRequest = Annotated[
    Union[
        VolcRequest, 
        KlingRequest, 
        MinimaxRequest, 
        DashScopeRequest, 
        MockRequest
    ],
    Field(discriminator="provider")
]
