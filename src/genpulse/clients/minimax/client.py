import asyncio
from loguru import logger
import os
import httpx
from typing import Optional, Dict, Any, Union, Callable, Literal
from genpulse.clients.base import BaseClient
from .schemas import (
    MinimaxVideoParams,
    MinimaxVideoResponse,
    MinimaxTaskStatusResponse,
    MinimaxFileResponse,
    MinimaxImageParams,
    MinimaxImageResponse,
    MinimaxSpeechParams,
    MinimaxSpeechResponse,
    MinimaxSpeechStatusResponse,
    GetVoiceResp
)


class MinimaxClient(BaseClient):
    """
    MiniMax API Client for Video, Image and Speech Generation.
    Supports task submission, status polling, and file retrieval.
    """

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        super().__init__(base_url=base_url or "https://api.minimaxi.com")
        self.api_key = api_key or os.getenv('MINIMAX_API_KEY')
        if not self.api_key:
            raise ValueError("MiniMax API Key is missing.")
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def _get_headers(self) -> Dict[str, str]:
        """Return the fixed headers for MiniMax API"""
        return self.headers

    # --- Common Methods ---

    async def get_file_info(self, file_id: Union[str, int]) -> MinimaxFileResponse:
        """Retrieve file details, mainly the download URL."""
        data = await self._request("GET", f"/v1/files/retrieve?file_id={file_id}")
        return MinimaxFileResponse(**data)

    # --- Video Generation Methods ---

    async def get_video_task(self, task_id: str) -> MinimaxTaskStatusResponse:
        """
        Query the status of a video generation task.
        If successful, automatically fetches the download_url.
        """
        logger.info(f"Minimax: Querying video task status: {task_id}")
        data = await self._request("GET", f"/v1/query/video_generation?task_id={task_id}")
        
        status_resp = MinimaxTaskStatusResponse(**data)
        
        if status_resp.is_succeeded and status_resp.file_id:
            try:
                file_info = await self.get_file_info(status_resp.file_id)
                status_resp.download_url = file_info.file.download_url
            except Exception as e:
                logger.error(f"Minimax: Failed to retrieve file info for task {task_id}: {e}")
        
        return status_resp

    async def generate_video(
        self, 
        params: Union[Dict[str, Any], MinimaxVideoParams],
        wait: bool = True,
        callback: Optional[Callable] = None,
        polling_interval: int = 10,
        **kwargs
    ) -> MinimaxTaskStatusResponse:
        """
        Submit a video generation task (Text-to-Video / Image-to-Video).

        Args:
            params: Dictionary or Pydantic model containing task parameters.
            wait: Whether to wait for the task to complete.
            callback: Optional async callback for status updates.
            polling_interval: Interval in seconds for status checks (default 10).
            **kwargs: Additional arguments passed to the API client.

        Returns:
            MinimaxTaskStatusResponse: Final status of the task.
        """
        request = MinimaxVideoParams(**params) if isinstance(params, dict) else params
        request.callback_url = request.callback_url or self.callback_url
        request_data = request.model_dump(exclude_none=True)
        
        logger.info(f"Minimax: Submitting video generation task (Model: {request.model})")
        
        data = await self._request("POST", "/v1/video_generation", json=request_data, **kwargs)
        init_resp = MinimaxVideoResponse(**data)
        
        if init_resp.base_resp.status_code != 0:
            logger.error(f"Minimax: Video creation failed: {init_resp.base_resp.status_msg}")
            raise Exception(f"MiniMax Error ({init_resp.base_resp.status_code}): {init_resp.base_resp.status_msg}")
            
        task_id = init_resp.task_id
        
        if not wait:
            return MinimaxTaskStatusResponse(
                task_id=task_id,
                status="Preparing",
                base_resp=init_resp.base_resp
            )

        return await self.poll_task(
            task_id=task_id,
            get_status_func=self.get_video_task,
            check_success_func=lambda resp: resp.is_succeeded,
            check_failed_func=lambda resp: resp.is_finished and not resp.is_succeeded,
            callback=callback,
            timeout=1200,
            interval=polling_interval
        )

    # --- Image Generation Methods ---

    async def generate_image(
        self, 
        params: Union[Dict[str, Any], MinimaxImageParams],
        **kwargs
    ) -> MinimaxImageResponse:
        """
        Submit an image generation task (Text-to-Image / Image-to-Image).
        This is typically a synchronous call returning image URLs directly.

        Args:
            params: Dictionary or Pydantic model containing task parameters.
            **kwargs: Additional arguments passed to the API client.

        Returns:
            MinimaxImageResponse: Response containing generated image URLs.
        """
        request = MinimaxImageParams(**params) if isinstance(params, dict) else params
        request_data = request.model_dump(exclude_none=True)
        
        logger.info(f"Minimax: Submitting image generation task (Model: {request.model})")
        
        data = await self._request("POST", "/v1/image_generation", json=request_data, **kwargs)
        resp = MinimaxImageResponse(**data)
        
        if not resp.is_succeeded:
            logger.error(f"Minimax: Image creation failed: {resp.base_resp.status_msg}")
            raise Exception(f"MiniMax Error ({resp.base_resp.status_code}): {resp.base_resp.status_msg}")
            
        return resp

    # --- Speech (T2A) Generation Methods ---

    async def get_speech_task(self, task_id: str) -> MinimaxSpeechStatusResponse:
        """Fetch the status of an asynchronous speech synthesis task"""
        logger.info(f"Minimax: Querying speech task status: {task_id}")
        data = await self._request("GET", f"/v1/query/t2a_async_query_v2?task_id={task_id}")
        
        status_resp = MinimaxSpeechStatusResponse(**data)
        
        # If task is successful, fetch the file details to get the download URL
        if status_resp.is_succeeded and status_resp.file_id:
            try:
                file_info = await self.get_file_info(status_resp.file_id)
                status_resp.download_url = file_info.file.download_url
            except Exception as e:
                logger.error(f"Minimax: Failed to retrieve file info for speech task {task_id}: {e}")
                
        return status_resp

    async def generate_speech(
        self, 
        params: Union[Dict[str, Any], MinimaxSpeechParams],
        wait: bool = True,
        callback: Optional[Callable] = None,
        polling_interval: int = 10,
        **kwargs
    ) -> MinimaxSpeechStatusResponse:
        """
        Submit a long text-to-speech task and optionally poll for completion.

        Args:
            params: Dictionary or Pydantic model containing task parameters.
            wait: Whether to wait for the task to complete.
            callback: Optional async callback for status updates.
            polling_interval: Interval in seconds for status checks (default 10).
            **kwargs: Additional arguments passed to the API client.

        Returns:
            MinimaxSpeechStatusResponse: Final status of the task involving audio download URL.
        """
        request = MinimaxSpeechParams(**params) if isinstance(params, dict) else params
        request_data = request.model_dump(exclude_none=True)
        
        logger.info(f"Minimax: Submitting speech generation task (Model: {request.model})")
        
        data = await self._request("POST", "/v1/t2a_async_v2", json=request_data, **kwargs)
        init_resp = MinimaxSpeechResponse(**data)
        
        if init_resp.base_resp.status_code != 0:
            logger.error(f"Minimax: Speech creation failed: {init_resp.base_resp.status_msg}")
            raise Exception(f"MiniMax Error ({init_resp.base_resp.status_code}): {init_resp.base_resp.status_msg}")
            
        task_id = init_resp.task_id
        
        if not wait:
            return MinimaxSpeechStatusResponse(
                task_id=task_id,
                status="processing",
                base_resp=init_resp.base_resp
            )

        return await self.poll_task(
            task_id=task_id,
            get_status_func=self.get_speech_task,
            check_success_func=lambda resp: resp.is_succeeded,
            check_failed_func=lambda resp: resp.is_finished and not resp.is_succeeded,
            callback=callback,
            timeout=1800, # Long text might take longer
            interval=polling_interval
        )

    # --- Voice Management Methods ---

    async def get_voices(
        self, 
        voice_type: Literal["system", "voice_cloning", "voice_generation", "all"] = "all"
    ) -> GetVoiceResp:
        """
        Query available voice IDs by type.
        """
        logger.info(f"Minimax: Querying available voices (Type: {voice_type})")
        data = await self._request("POST", "/v1/get_voice", json={"voice_type": voice_type})
        resp = GetVoiceResp(**data)
        
        if resp.base_resp.status_code != 0:
            logger.error(f"Minimax: Get voice failed: {resp.base_resp.status_msg}")
            raise Exception(f"MiniMax Error ({resp.base_resp.status_code}): {resp.base_resp.status_msg}")
            
        return resp

def create_minimax_client(api_key: Optional[str] = None, base_url: Optional[str] = None) -> MinimaxClient:
    """Factory function for MinimaxClient"""
    return MinimaxClient(api_key=api_key, base_url=base_url)

