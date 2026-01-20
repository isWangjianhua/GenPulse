from typing import Optional, List, Literal, Any, Union, Dict
from pydantic import BaseModel, Field

# --- Response Base ---

class BaseResp(BaseModel):
    status_code: int
    status_msg: str

# --- Video Schemas ---

class SubjectReference(BaseModel):
    """Subject reference for character-consistent video generation"""
    type: str = "character"
    image: List[str] = Field(..., description="List of reference images (currently only 1 supported)")

class MinimaxVideoParams(BaseModel):
    """
    MiniMax Video Generation Parameters.
    Unified schema for text-to-video, image-to-video, and subject-reference.
    """
    model: str = Field(..., description="Model ID, e.g., 'MiniMax-Hailuo-2.3', 'S2V-01', etc.")
    prompt: str = Field(..., max_length=2000)
    
    # Image references
    first_frame_image: Optional[str] = None
    last_frame_image: Optional[str] = None
    subject_reference: Optional[List[SubjectReference]] = None

    # Common parameters
    prompt_optimizer: bool = True
    fast_pretreatment: bool = False
    duration: Optional[int] = 6
    resolution: Optional[Literal["512P", "720P", "768P", "1080P"]] = "768P"
    callback_url: Optional[str] = None
    aigc_watermark: bool = False

    class Config:
        extra = "allow"

class MinimaxVideoResponse(BaseModel):
    """Initial task creation response for Video"""
    task_id: str
    base_resp: BaseResp

class MinimaxTaskStatusResponse(BaseModel):
    """Detailed task status response from querying (Video)"""
    task_id: str
    status: Literal["Preparing", "Queueing", "Processing", "Success", "Fail"]
    file_id: Optional[str] = None
    video_width: Optional[int] = None
    video_height: Optional[int] = None
    base_resp: BaseResp
    download_url: Optional[str] = None

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
    style_type: Literal["漫画", "元气", "中世�?, "水彩"]
    style_weight: float = 0.8

class ImageSubjectReference(BaseModel):
    """Subject reference for image-to-image generation"""
    type: str = "character"
    image_file: str = Field(..., description="URL or Base64 of the reference image")

class MinimaxImageParams(BaseModel):
    """MiniMax Image Generation Parameters (Text-to-Image / Image-to-Image)"""
    model: Literal["image-01", "image-01-live"] = "image-01"
    prompt: str = Field(..., max_length=1500)
    style: Optional[StyleObject] = None
    subject_reference: Optional[List[ImageSubjectReference]] = None
    aspect_ratio: Optional[Literal["1:1", "16:9", "4:3", "3:2", "2:3", "3:4", "9:16", "21:9"]] = "1:1"
    width: Optional[int] = None
    height: Optional[int] = None
    response_format: Literal["url", "base64"] = "url"
    seed: Optional[int] = None
    n: int = Field(1, ge=1, le=9)
    prompt_optimizer: bool = False
    aigc_watermark: bool = False

    class Config:
        extra = "allow"

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
    voice_id: str
    speed: float = 1.0
    vol: float = 1.0
    pitch: int = 0
    emotion: Optional[Literal["happy", "sad", "angry", "fearful", "disgusted", "surprised", "calm", "fluent", "whisper"]] = None
    english_normalization: bool = False

class AudioSetting(BaseModel):
    audio_sample_rate: int = 32000
    bitrate: int = 128000
    format: Literal["mp3", "pcm", "flac"] = "mp3"
    channel: int = 2

class PronunciationDict(BaseModel):
    tone: List[str] = []

class VoiceModify(BaseModel):
    pitch: int = Field(0, ge=-100, le=100)
    intensity: int = Field(0, ge=-100, le=100)
    timbre: int = Field(0, ge=-100, le=100)
    sound_effects: Optional[Literal["spacious_echo", "auditorium_echo", "lofi_telephone", "robotic"]] = None

class MinimaxSpeechParams(BaseModel):
    """MiniMax Text-to-Audio Async V2 Parameters"""
    model: str = "speech-2.6-hd"
    text: Optional[str] = Field(None, max_length=50000)
    text_file_id: Optional[int] = None
    voice_setting: VoiceSetting
    audio_setting: Optional[AudioSetting] = AudioSetting()
    pronunciation_dict: Optional[PronunciationDict] = None
    language_boost: Optional[str] = None
    voice_modify: Optional[VoiceModify] = None
    aigc_watermark: bool = False

    class Config:
        extra = "allow"

class MinimaxSpeechResponse(BaseModel):
    """Initial task creation response for Speech"""
    task_id: str
    file_id: Optional[int] = None
    task_token: Optional[str] = None
    usage_characters: Optional[int] = None
    base_resp: BaseResp

class MinimaxSpeechStatusResponse(BaseModel):
    """Detailed task status response from querying (Speech)"""
    task_id: str
    status: Literal["processing", "success", "failed", "expired", "Processing", "Success", "Failed", "Expired"]
    file_id: Optional[int] = None
    base_resp: BaseResp
    download_url: Optional[str] = None

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

