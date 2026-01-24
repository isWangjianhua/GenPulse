import asyncio
import os
from typing import Optional, Dict, Any, Union, Callable
from loguru import logger
from volcenginesdkarkruntime import Ark
from .schemas import (
    VolcImageParams, 
    VolcVideoParams, 
    ArkResponse, 
    VolcVideoStatusResponse
)

from genpulse.clients.base import BaseClient

class VolcEngineClient(BaseClient):
    """
    VolcEngine Ark Service Client
    Inherits polling capabilities from BaseClient.
    """

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key or os.getenv('ARK_API_KEY')
        if not self.api_key:
            raise ValueError("VolcEngine API Key is missing.")
            
        self.base_url = base_url or "https://ark.cn-beijing.volces.com/api/v3"
        self.client = Ark(
            base_url=self.base_url,
            api_key=self.api_key
        )

    async def generate_image(
        self, 
        params: Union[Dict[str, Any], VolcImageParams],
        **kwargs
    ) -> ArkResponse:
        """
        Text-to-Image / Image-to-Image (Synchronous API).

        Args:
            params: Dictionary or Pydantic model containing task parameters.
            **kwargs: Additional arguments passed to the SDK.

        Returns:
            ArkResponse: Synchronous response containing generated images.
        """
        request = VolcImageParams(**params) if isinstance(params, dict) else params
        request_data = request.model_dump(exclude_none=True, mode="json")
        
        logger.info(f"Volcengine: Sending image generation request: {request_data}")
        
        sdk_args = {**request_data, **kwargs}
        
        response = await asyncio.to_thread(
            self.client.images.generate,
            **sdk_args
        )
        
        resp_dict = response.model_dump() if hasattr(response, 'model_dump') else response.__dict__
        return ArkResponse(**resp_dict)

    async def get_video_task(self, task_id: str) -> VolcVideoStatusResponse:
        """Query the current status of a video task"""
        response = await asyncio.to_thread(
            self.client.content_generation.tasks.get,
            task_id=task_id
        )
        resp_dict = response.model_dump() if hasattr(response, 'model_dump') else response.__dict__
        return VolcVideoStatusResponse(**resp_dict)

    async def generate_video(
        self, 
        params: Union[Dict[str, Any], VolcVideoParams],
        wait: bool = True,
        callback: Optional[Callable] = None,
        polling_interval: int = 5,
        **kwargs
    ) -> VolcVideoStatusResponse:
        """
        Create a video task and optionally poll for completion.

        Args:
            params: Dictionary or Pydantic model containing task parameters.
            wait: Whether to wait for the task to complete.
            callback: Optional async callback for status updates.
            polling_interval: Interval in seconds for status checks (default 5).
            **kwargs: Additional arguments passed to the SDK.

        Returns:
            VolcVideoStatusResponse: Final status of the task.
        """
        # 1. Create the task
        request = VolcVideoParams(**params) if isinstance(params, dict) else params
        request_data = request.model_dump(exclude_none=True, mode="json")
        
        logger.info(f"Volcengine: Creating video generation task: {request_data}")
        
        sdk_args = {**request_data, **kwargs}

        creation_resp = await asyncio.to_thread(
            self.client.content_generation.tasks.create,
            **sdk_args
        )
        task_id = creation_resp.id
        
        if not wait:
            return VolcVideoStatusResponse(id=task_id, status="queued")

        # 2. Use BaseClient's generic polling
        return await self.poll_task(
            task_id=task_id,
            get_status_func=self.get_video_task,
            check_success_func=lambda resp: resp.status == "succeeded",
            check_failed_func=lambda resp: resp.status in ["failed", "cancelled", "expired"],
            callback=callback,
            timeout=600,  # Video generation might be slow
            interval=polling_interval
        )

def create_volcengine_client(api_key: Optional[str] = None, base_url: Optional[str] = None) -> VolcEngineClient:
    """
    Factory function to create a VolcEngineClient instance.
    """
    return VolcEngineClient(api_key=api_key, base_url=base_url)
