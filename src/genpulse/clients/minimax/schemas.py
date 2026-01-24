from typing import Optional, List, Literal, Any, Union, Dict
from pydantic import BaseModel, Field, ConfigDict

# --- Response Base ---

class BaseResp(BaseModel):
    status_code: int = Field(..., description="API Status Code (0=Success)")
    status_msg: str = Field(..., description="API Status Message")

# --- Video Schemas ---

class SubjectReference(BaseModel):
    """Subject reference for character-consistent video generation"""
    type: str = "character"
    image: List[str] = Field(..., description="List of reference images (currently only 1 supported)")

class MinimaxVideoParams(BaseModel):
    """
    Parameters for MiniMax video generation tasks.
    Supports Text-to-Video, Image-to-Video, and parameter tuning.
    
    Args:
        model: Model identifier ('S2V-01', 'MiniMax-Hailuo-2.3').
        prompt: Video description (max 2000 chars).
        duration: Video duration (usually 6 seconds).
    """
    model: str = Field(..., description="Model ID, e.g., 'MiniMax-Hailuo-2.3', 'S2V-01', etc.")
    prompt: str = Field(..., max_length=2000, description="Prompt text")
    
    # Image references
    first_frame_image: Optional[str] = Field(None, description="Start frame image")
    last_frame_image: Optional[str] = Field(None, description="End frame image")
    subject_reference: Optional[List[SubjectReference]] = Field(None, description="Character consistency ref")

    # Common parameters
    prompt_optimizer: bool = Field(True, description="Optimize prompt")
    fast_pretreatment: bool = False
    duration: Optional[int] = Field(6, description="Duration in seconds")
    resolution: Optional[Literal["512P", "720P", "768P", "1080P"]] = "768P"
    callback_url: Optional[str] = None
    aigc_watermark: bool = False

    model_config = ConfigDict(extra="allow")

class MinimaxVideoResponse(BaseModel):
    """Initial task creation response for Video"""
    task_id: str = Field(..., description="Task ID")
    base_resp: BaseResp = Field(..., description="Base response status")

class MinimaxTaskStatusResponse(BaseModel):
    """Detailed task status response from querying (Video)"""
    task_id: str = Field(..., description="Task ID")
    status: Literal["Preparing", "Queueing", "Processing", "Success", "Fail"] = Field(..., description="Task status")
    file_id: Optional[str] = Field(None, description="Generated File ID")
    video_width: Optional[int] = Field(None, description="Video width")
    video_height: Optional[int] = Field(None, description="Video height")
    base_resp: BaseResp = Field(..., description="Base response status")
    download_url: Optional[str] = Field(None, description="Video download URL (fetched separately)")

    @property
    def is_finished(self) -> bool:
        return self.status in ["Success", "Fail"]

    @property
    def is_succeeded(self) -> bool:
        return self.status == "Success"

class FileObject(BaseModel):
    """File details provided after successful generation"""
    file_id: Union[str, int]
    bytes: Optional[int] = None
    created_at: Optional[int] = None
    filename: Optional[str] = None
    purpose: Optional[str] = None
    download_url: str

class MinimaxFileResponse(BaseModel):
    """File info response from /v1/files/retrieve"""
    file: FileObject
    base_resp: BaseResp

# --- Image Schemas ---

class StyleObject(BaseModel):
    """Style settings for image-01-live"""
    style_type: Literal["漫画", "元气", "中世纪", "水彩"]
    style_weight: float = 0.8

class ImageSubjectReference(BaseModel):
    """Subject reference for image-to-image generation"""
    type: str = "character"
    image_file: str = Field(..., description="URL or Base64 of the reference image")

class MinimaxImageParams(BaseModel):
    """
    Parameters for MiniMax image generation tasks.
    
    Args:
        model: Model ID ('image-01').
        prompt: Image description.
        n: Number of images (1-9).
    """
    model: Literal["image-01", "image-01-live"] = Field("image-01", description="Model ID")
    prompt: str = Field(..., max_length=1500, description="Image prompt")
    style: Optional[StyleObject] = Field(None, description="Style settings (image-01-live only)")
    subject_reference: Optional[List[ImageSubjectReference]] = Field(None, description="Subject reference")
    aspect_ratio: Optional[Literal["1:1", "16:9", "4:3", "3:2", "2:3", "3:4", "9:16", "21:9"]] = "1:1"
    width: Optional[int] = None
    height: Optional[int] = None
    response_format: Literal["url", "base64"] = "url"
    seed: Optional[int] = None
    n: int = Field(1, ge=1, le=9, description="Number of images")
    prompt_optimizer: bool = False
    aigc_watermark: bool = False

    model_config = ConfigDict(extra="allow")

class ImageDataObject(BaseModel):
    """Output data for image generation"""
    image_urls: Optional[List[str]] = None
    image_base64: Optional[List[str]] = None

class ImageMetadata(BaseModel):
    success_count: int
    failed_count: int

class MinimaxImageResponse(BaseModel):
    """Response for image generation"""
    id: str
    data: Optional[ImageDataObject] = None
    metadata: Optional[ImageMetadata] = None
    base_resp: BaseResp

    @property
    def is_succeeded(self) -> bool:
        return self.base_resp.status_code == 0

# --- Speech (T2A) Schemas ---

class VoiceSetting(BaseModel):
    voice_id: str = Field(..., description="Voice ID to use")
    speed: float = Field(1.0, description="Speed multiplier (0.5-2.0)")
    vol: float = Field(1.0, description="Volume multiplier (0-10)")
    pitch: int = Field(0, description="Pitch adjustment (-12 to 12)")
    emotion: Optional[Literal["happy", "sad", "angry", "fearful", "disgusted", "surprised", "calm", "fluent", "whisper"]] = Field(None, description="Emotion style")
    english_normalization: bool = Field(False, description="Normalize English numbers/dates")

class AudioSetting(BaseModel):
    audio_sample_rate: int = Field(32000, description="Sample rate (e.g. 32000)")
    bitrate: int = Field(128000, description="Bitrate (e.g. 128000)")
    format: Literal["mp3", "pcm", "flac"] = Field("mp3", description="Audio format")
    channel: int = Field(2, description="Channel count (1 or 2)")

class PronunciationDict(BaseModel):
    tone: List[str] = []

class VoiceModify(BaseModel):
    pitch: int = Field(0, ge=-100, le=100, description="Pitch modification")
    intensity: int = Field(0, ge=-100, le=100, description="Volume intensity")
    timbre: int = Field(0, ge=-100, le=100, description="Timbre adjustment")
    sound_effects: Optional[Literal["spacious_echo", "auditorium_echo", "lofi_telephone", "robotic"]] = Field(None, description="Post-processing effect")

class MinimaxSpeechParams(BaseModel):
    """
    Parameters for MiniMax Text-to-Audio (Speech) generation.
    """
    model: str = Field("speech-2.6-hd", description="Model ID")
    text: Optional[str] = Field(None, max_length=50000, description="Text to speak")
    text_file_id: Optional[int] = Field(None, description="File ID containing text")
    voice_setting: VoiceSetting = Field(..., description="Voice configuration")
    audio_setting: Optional[AudioSetting] = Field(AudioSetting(), description="Audio format settings")
    pronunciation_dict: Optional[PronunciationDict] = None
    language_boost: Optional[str] = Field(None, description="Language optimization (e.g., 'auto', 'en', 'cn')")
    voice_modify: Optional[VoiceModify] = None
    aigc_watermark: bool = False

    model_config = ConfigDict(extra="allow")

class MinimaxSpeechResponse(BaseModel):
    """Initial task creation response for Speech"""
    task_id: str = Field(..., description="Task ID")
    file_id: Optional[int] = Field(None, description="File ID")
    task_token: Optional[str] = Field(None, description="Task Token")
    usage_characters: Optional[int] = Field(None, description="Characters used")
    base_resp: BaseResp = Field(..., description="Base response status")

class MinimaxSpeechStatusResponse(BaseModel):
    """Detailed task status response from querying (Speech)"""
    task_id: str = Field(..., description="Task ID")
    status: Literal["processing", "success", "failed", "expired", "Processing", "Success", "Failed", "Expired"] = Field(..., description="Task status")
    file_id: Optional[int] = Field(None, description="File ID")
    base_resp: BaseResp = Field(..., description="Base response status")
    download_url: Optional[str] = Field(None, description="Download URL if successful")

    @property
    def is_finished(self) -> bool:
        s = self.status.lower()
        return s in ["success", "failed", "expired"]

    @property
    def is_succeeded(self) -> bool:
        return self.status.lower() == "success"

# --- Voice Management Schemas ---

class SystemVoiceInfo(BaseModel):
    voice_id: str
    voice_name: str
    description: List[str] = []

class VoiceCloningInfo(BaseModel):
    voice_id: str
    created_time: str
    description: List[str] = []

class VoiceGenerationInfo(BaseModel):
    voice_id: str
    created_time: str
    description: List[str] = []

class GetVoiceResp(BaseModel):
    """Response for /v1/get_voice"""
    system_voice: Optional[List[SystemVoiceInfo]] = None
    voice_cloning: Optional[List[VoiceCloningInfo]] = None
    voice_generation: Optional[List[VoiceGenerationInfo]] = None
    base_resp: BaseResp

