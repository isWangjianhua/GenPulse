from typing import Optional, List, Literal, Any, Dict
from pydantic import BaseModel, Field, model_validator, ConfigDict

# --- Common Components ---

class TencentTaskResponse(BaseModel):
    """Initial response for task creation"""
    TaskId: str = Field(..., description="The unique ID of the task")
    RequestId: str = Field(..., description="The unique request ID")

# --- Video Generation Schemas ---

class AigcVideoTaskInputFileInfo(BaseModel):
    """Input asset information for AIGC video generation task"""
    Type: Literal["File", "Url"] = Field("Url", description="Resource type: 'File' (VOD File ID) or 'Url' (External URL)")
    Category: Optional[Literal["Image", "Video"]] = Field("Image", description="Asset category: 'Image' or 'Video'")
    FileId: Optional[str] = Field(None, description="VOD File ID, required if Type is 'File'")
    Url: Optional[str] = Field(None, description="Asset URL, required if Type is 'Url'")
    ReferenceType: Optional[Literal["asset", "style"]] = Field(None, description="Reference type: 'asset' (Subject/Person) or 'style' (Artistic style)")
    ObjectId: Optional[str] = Field(None, description="Subject ID. Vidu models support 1-7 images as subject references via this field")
    VoiceId: Optional[str] = Field(None, description="Voice ID for human-driven video generation in supported models")

class AigcVideoOutputConfig(BaseModel):
    """Output configuration for video generation task"""
    StorageMode: Literal["Permanent", "Temporary"] = Field("Temporary", description="Storage mode: 'Permanent' or 'Temporary'")
    MediaName: Optional[str] = Field(None, description="Name of the output media file")
    ClassId: Optional[int] = Field(0, description="Category/Class ID for the organized storage")
    ExpireTime: Optional[str] = Field(None, description="Expiration time in ISO format, only valid for Temporary storage")
    Resolution: Optional[str] = Field(None, description="Output resolution, e.g., '1080P', '720P'")
    AspectRatio: Optional[str] = Field(None, description="Aspect ratio, e.g., '16:9', '9:16', '1:1'")
    AudioGeneration: Optional[Literal["Enabled", "Disabled"]] = Field("Disabled", description="Whether to generate audio for the video")
    PersonGeneration: Optional[Literal["AllowAdult", "Disallowed"]] = Field(None, description="Human generation policy: 'AllowAdult' or 'Disallowed'")
    InputComplianceCheck: Optional[Literal["Enabled", "Disabled"]] = Field("Enabled", description="Whether to perform compliance check on input assets")
    OutputComplianceCheck: Optional[Literal["Enabled", "Disabled"]] = Field("Enabled", description="Whether to perform compliance check on generated output")
    EnhanceSwitch: Optional[Literal["Enabled", "Disabled"]] = Field(None, description="Switch for quality enhancement/upscaling")

class TencentVideoParams(BaseModel):
    """Request parameters for CreateAigcVideoTask API"""
    model_config = ConfigDict(extra="allow")
    
    SubAppId: Optional[int] = Field(None, description="VOD Application ID")
    ModelName: Literal["Hailuo", "Kling", "Jimeng", "Vidu", "Hunyuan", "Mingmou", "GV", "OS"] = Field(..., description="Model name")
    ModelVersion: str = Field(..., description="Model version")
    FileInfos: Optional[List[AigcVideoTaskInputFileInfo]] = Field(None, description="List of input assets (max 3 for most models)")
    LastFrameFileId: Optional[str] = Field(None, description="Media File ID for the tail frame (end frame)")
    LastFrameUrl: Optional[str] = Field(None, description="Media URL for the tail frame (end frame)")
    Prompt: Optional[str] = Field(None, description="Prompt for video generation")
    NegativePrompt: Optional[str] = Field(None, description="Terms to prevent in the generated video")
    EnhancePrompt: Optional[Literal["Enabled", "Disabled"]] = Field("Disabled", description="Automatic prompt optimization")
    OutputConfig: Optional[AigcVideoOutputConfig] = Field(None, description="Output configuration")
    InputRegion: Optional[Literal["Oversea", "Mainland"]] = Field("Mainland", description="Region of input files. Choose 'Oversea' for non-Mainland URLs")
    SceneType: Optional[str] = Field(None, description="Scene type, e.g., 'motion_control' for Kling")
    SessionId: Optional[str] = Field(None, description="Idempotency key for deduplication (valid for 3 days)")
    SessionContext: Optional[str] = Field(None, description="Context for transparency/tracking in callbacks")
    TasksPriority: Optional[int] = Field(0, description="Task priority from -10 to 10. Higher value means higher priority")
    ExtInfo: Optional[str] = Field(None, description="Reserved field for special purposes")

# --- Image Generation Schemas ---

class TencentAigcImageInputFileInfo(BaseModel):
    """Input image information for AIGC image generation task"""
    Type: Literal["File", "Url"] = Field("Url", description="Resource type")
    FileId: Optional[str] = Field(None, description="VOD File ID")
    Url: Optional[str] = Field(None, description="Image URL")
    Text: Optional[str] = Field(None, description="Reference text (if supported by model)")

class TencentAigcImageOutputConfig(BaseModel):
    """Output configuration for image generation task"""
    StorageMode: Literal["Permanent", "Temporary"] = Field("Temporary", description="Storage mode")
    MediaName: Optional[str] = Field(None, description="Output filename")
    Resolution: Optional[str] = Field(None, description="Output resolution")
    AspectRatio: Optional[str] = Field(None, description="Aspect ratio")
    PersonGeneration: Optional[Literal["AllowAdult", "Disallowed"]] = Field(None, description="Human generation policy")
    InputComplianceCheck: Optional[Literal["Enabled", "Disabled"]] = Field("Enabled", description="Input compliance check")
    OutputComplianceCheck: Optional[Literal["Enabled", "Disabled"]] = Field("Enabled", description="Output compliance check")

class TencentImageParams(BaseModel):
    """Request parameters for CreateAigcImageTask API"""
    model_config = ConfigDict(extra="allow")
    
    SubAppId: Optional[int] = Field(None, description="VOD Application ID")
    ModelName: Literal["GEM", "Qwen", "Hunyuan"] = Field("Hunyuan", description="Model name")
    ModelVersion: str = Field("3.0", description="Model version")
    FileInfos: Optional[List[TencentAigcImageInputFileInfo]] = Field(None, description="List of input assets")
    Prompt: Optional[str] = Field(None, description="Prompt for image generation (required if FileInfos is empty)")
    NegativePrompt: Optional[str] = Field(None, description="Negative prompt")
    EnhancePrompt: Optional[Literal["Enabled", "Disabled"]] = Field("Disabled", description="Whether to optimize the prompt automatically")
    OutputConfig: Optional[TencentAigcImageOutputConfig] = Field(None, description="Output configuration")
    SessionId: Optional[str] = Field(None, description="Idempotency key")
    SessionContext: Optional[str] = Field(None, description="Callback context")
    TasksPriority: Optional[int] = Field(0, description="Task priority")
    ExtInfo: Optional[str] = Field(None, description="Reserved field")

# --- Task Query Schemas (DescribeTaskDetail) ---

class AigcTaskResult(BaseModel):
    """Specific result details for an AIGC task"""
    FileId: Optional[str] = Field(None, description="The ID of the generated file in VOD")
    FileUrl: Optional[str] = Field(None, description="The public URL of the generated file")
    ImageUrl: Optional[str] = Field(None, alias="FileUrl", description="Mapping for image generation result URL")
    ExpireTime: Optional[str] = Field(None, description="Expiration time of the URL")
    FileInfos: Optional[List[Dict[str, Any]]] = Field(None, description="Array of file information objects")

class AigcTaskDetail(BaseModel):
    """Internal task details returned by DescribeTaskDetail"""
    TaskId: str = Field(..., description="Internal sub-task ID")
    Status: str = Field(..., description="Internal sub-task status")
    ErrCode: int = Field(0, description="Error code. 0 indicates success")
    Message: str = Field("", description="Error message if any")
    Progress: int = Field(0, description="Task progress percentage (0-100)")
    Input: Optional[Dict[str, Any]] = Field(None, description="Original input parameters for the task")
    Output: Optional[AigcTaskResult] = Field(None, description="The output result of the task")

class TencentTaskDetailResponse(BaseModel):
    """Full response for the DescribeTaskDetail API"""
    TaskId: Optional[str] = Field(None, description="The unique ID of the overall task (might not be present in top level)")
    TaskType: str = Field(..., description="The type of the task (e.g., AigcVideoTask, AigcImageTask)")
    Status: Literal["WAITING", "PROCESSING", "FINISH", "ABORTED"] = Field(..., description="Global task status")
    CreateTime: str = Field(..., description="Task creation time in ISO format")
    BeginProcessTime: Optional[str] = Field(None, description="Time when task processing started")
    FinishTime: Optional[str] = Field(None, description="Time when task processing finished")
    
    # Specific task details corresponding to TaskType
    AigcVideoTask: Optional[AigcTaskDetail] = Field(None, description="Details for video generation task")
    AigcImageTask: Optional[AigcTaskDetail] = Field(None, description="Details for image generation task")
    RequestId: str = Field(..., description="Unique request ID for troubleshooting")

    @model_validator(mode="after")
    def populate_task_id(self) -> "TencentTaskDetailResponse":
        """Attempt to populate TaskId from nested tasks if missing at top level"""
        if not self.TaskId:
            if self.AigcVideoTask:
                self.TaskId = self.AigcVideoTask.TaskId
            elif self.AigcImageTask:
                self.TaskId = self.AigcImageTask.TaskId
        return self

    @property
    def is_finished(self) -> bool:
        """Determines if the task has reached a terminal state (Success or Error)"""
        return self.Status in ["FINISH", "ABORTED"]

    @property
    def is_succeeded(self) -> bool:
        """Determines if the task completed successfully without internal errors"""
        if self.Status != "FINISH":
            return False
            
        # Verify internal error codes for AIGC tasks if applicable
        if self.AigcVideoTask and self.AigcVideoTask.ErrCode != 0:
            return False
        if self.AigcImageTask and self.AigcImageTask.ErrCode != 0:
            return False
            
        return True

    @property
    def result_url(self) -> Optional[str]:
        """Conveniently extracts the final product URL from the task details"""
        # Video tasks: check Output.FileInfos array
        if self.AigcVideoTask and self.AigcVideoTask.Output:
            file_infos = self.AigcVideoTask.Output.FileInfos
            if file_infos and len(file_infos) > 0:
                return file_infos[0].get("FileUrl")
        
        # Image tasks: check Output.FileInfos array  
        if self.AigcImageTask and self.AigcImageTask.Output:
            file_infos = self.AigcImageTask.Output.FileInfos
            if file_infos and len(file_infos) > 0:
                return file_infos[0].get("FileUrl")
        
        return None
