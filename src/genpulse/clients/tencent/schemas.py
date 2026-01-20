from typing import Optional, List, Literal, Any, Dict
from pydantic import BaseModel, Field

# --- Common Components (Shared or similar between Image/Video) ---

class TencentVideoResult(BaseModel):
    """Result details when video task is DONE"""
    Url: str
    Size: Optional[int] = None
    Duration: Optional[float] = None

class TencentAigcImageResult(BaseModel):
    """Result details when image task is DONE"""
    Url: str
    FileId: Optional[str] = None

# --- Video Schemas ---

class AigcVideoTaskInputFileInfo(BaseModel):
    """Input file info for AIGC video task"""
    Type: Literal["File", "Url"] = "Url"
    Category: Optional[Literal["Image", "Video"]] = "Image"
    FileId: Optional[str] = None
    Url: Optional[str] = None
    ReferenceType: Optional[Literal["asset", "style"]] = None
    ObjectId: Optional[str] = None
    VoiceId: Optional[str] = None

class AigcVideoOutputConfig(BaseModel):
    """Output config for AIGC video task"""
    StorageMode: Literal["Permanent", "Temporary"] = "Temporary"
    MediaName: Optional[str] = None
    ClassId: Optional[int] = 0
    ExpireTime: Optional[str] = None
    Duration: Optional[float] = None
    Resolution: Optional[str] = None
    AspectRatio: Optional[str] = None
    AudioGeneration: Optional[Literal["Enabled", "Disabled"]] = "Disabled"
    PersonGeneration: Optional[Literal["AllowAdult", "Disallowed"]] = None
    InputComplianceCheck: Optional[Literal["Enabled", "Disabled"]] = "Enabled"
    OutputComplianceCheck: Optional[Literal["Enabled", "Disabled"]] = "Enabled"
    EnhanceSwitch: Optional[Literal["Enabled", "Disabled"]] = None
    FrameInterpolate: Optional[Literal["Enabled", "Disabled"]] = None

class TencentVideoParams(BaseModel):
    """Parameters for CreateAigcVideoTask"""
    SubAppId: Optional[int] = None
    ModelName: Literal["Hailuo", "Kling", "Jimeng", "Vidu", "Hunyuan", "Mingmou", "GV", "OS"]
    ModelVersion: str
    FileInfos: Optional[List[AigcVideoTaskInputFileInfo]] = None
    LastFrameFileId: Optional[str] = None
    LastFrameUrl: Optional[str] = None
    Prompt: Optional[str] = None
    NegativePrompt: Optional[str] = None
    EnhancePrompt: Optional[Literal["Enabled", "Disabled"]] = "Disabled"
    OutputConfig: Optional[AigcVideoOutputConfig] = None
    InputRegion: Optional[Literal["Oversea", "Mainland"]] = "Mainland"
    SceneType: Optional[str] = None
    SessionId: Optional[str] = None
    SessionContext: Optional[str] = None
    TasksPriority: Optional[int] = 0
    ExtInfo: Optional[str] = None

    class Config:
        extra = "allow"

class TencentVideoResponse(BaseModel):
    """Initial response for video task creation"""
    TaskId: str
    RequestId: str

class TencentStatusResponse(BaseModel):
    """Response for DescribeAigcVideoTask"""
    TaskId: str
    Status: Literal["WAIT", "RUN", "FAIL", "DONE"]
    Progress: Optional[int] = None
    Message: Optional[str] = None
    Result: Optional[TencentVideoResult] = None
    RequestId: str

    @property
    def is_finished(self) -> bool:
        return self.Status in ["DONE", "FAIL"]

    @property
    def is_succeeded(self) -> bool:
        return self.Status == "DONE"

# --- Image Schemas ---

class TencentAigcImageInputFileInfo(BaseModel):
    """Input file info for AIGC image task"""
    Type: Literal["File", "Url"] = "Url"
    FileId: Optional[str] = None
    Url: Optional[str] = None
    Text: Optional[str] = None

class TencentAigcImageOutputConfig(BaseModel):
    """Output config for AIGC image task"""
    StorageMode: Literal["Permanent", "Temporary"] = "Temporary"
    MediaName: Optional[str] = None
    ClassId: Optional[int] = 0
    ExpireTime: Optional[str] = None
    Resolution: Optional[str] = None
    AspectRatio: Optional[str] = None
    PersonGeneration: Optional[Literal["AllowAdult", "Disallowed"]] = None
    InputComplianceCheck: Optional[Literal["Enabled", "Disabled"]] = "Enabled"
    OutputComplianceCheck: Optional[Literal["Enabled", "Disabled"]] = "Enabled"

class TencentImageParams(BaseModel):
    """Parameters for CreateAigcImageTask"""
    SubAppId: Optional[int] = None
    ModelName: Literal["GEM", "Qwen", "Hunyuan"] = "Hunyuan"
    ModelVersion: str = "3.0"
    FileInfos: Optional[List[TencentAigcImageInputFileInfo]] = None
    Prompt: Optional[str] = None
    NegativePrompt: Optional[str] = None
    EnhancePrompt: Optional[Literal["Enabled", "Disabled"]] = "Disabled"
    OutputConfig: Optional[TencentAigcImageOutputConfig] = None
    SessionId: Optional[str] = None
    SessionContext: Optional[str] = None
    TasksPriority: Optional[int] = 0

    class Config:
        extra = "allow"

class TencentImageStatusResponse(BaseModel):
    """Response for DescribeAigcImageTask"""
    TaskId: str
    Status: Literal["WAIT", "RUN", "FAIL", "DONE"]
    Progress: Optional[int] = None
    Message: Optional[str] = None
    Result: Optional[TencentAigcImageResult] = None
    RequestId: str

    @property
    def is_finished(self) -> bool:
        return self.Status in ["DONE", "FAIL"]

    @property
    def is_succeeded(self) -> bool:
        return self.Status == "DONE"

