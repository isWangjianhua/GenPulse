import asyncio
from loguru import logger
import os
import time
import httpx
import jwt
from typing import Optional, Dict, Any, Union, Callable
from genpulse.clients.base import BaseClient
from .schemas import (
    KlingTextToVideoParams,
    KlingImageToVideoParams,
    KlingMultiImageToVideoParams,
    KlingStatusResponse
)


class KlingClient(BaseClient):
    """
    Kling AI Service Client
    Explicitly separates text, image, and multi-image video generation for clarity and type safety.
    """

    def __init__(
        self, 
        ak: Optional[str] = None, 
        sk: Optional[str] = None, 
        base_url: Optional[str] = None
    ):
        super().__init__(base_url=base_url or "https://api.klingai.com")
        self.ak = ak or os.getenv('KLING_AK')
        self.sk = sk or os.getenv('KLING_SK')
        
        if not self.ak or not self.sk:
            raise ValueError("Kling AK and SK are required for authentication.")

    def _generate_token(self) -> str:
        """Dynamic JWT token generator for Kling AI API"""
        headers = {"alg": "HS256", "typ": "JWT"}
        payload = {
            "iss": self.ak,
            "exp": int(time.time()) + 1800,
            "nbf": int(time.time()) - 5
        }
        return jwt.encode(payload, self.sk, headers=headers)

    def _get_headers(self) -> Dict[str, str]:
        """Generate common headers with dynamic JWT for each request"""
        token = self._generate_token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

    # --- Public Methods ---

    async def get_video_task(self, task_id: str) -> KlingStatusResponse:
        """Query task status and result"""
        logger.info(f"Kling: Querying task {task_id}")
        data = await self._request("GET", f"/v1/videos/text2video/{task_id}")
        return KlingStatusResponse(**data)

    async def text_to_video(
        self, 
        params: Union[Dict[str, Any], KlingTextToVideoParams],
        wait: bool = True,
        callback: Optional[Callable] = None,
        polling_interval: int = 15,
        **kwargs
    ) -> KlingStatusResponse:
        """
        Text-to-Video generation.

        Args:
            params: Dictionary or Pydantic model containing task parameters.
            wait: Whether to wait for the task to complete.
            callback: Optional async callback for status updates.
            polling_interval: Interval in seconds for status checks (default 15).
            **kwargs: Additional arguments passed to the API client.

        Returns:
            KlingStatusResponse: Final status of the task.
        """
        return await self._generate_video_internal(
            endpoint="/v1/videos/text2video",
            params_model=KlingTextToVideoParams,
            params=params,
            wait=wait,
            callback=callback,
            polling_interval=polling_interval,
            **kwargs
        )

    async def image_to_video(
        self, 
        params: Union[Dict[str, Any], KlingImageToVideoParams],
        wait: bool = True,
        callback: Optional[Callable] = None,
        polling_interval: int = 15,
        **kwargs
    ) -> KlingStatusResponse:
        """
        Image-to-Video generation (Start frame / End frame).

        Args:
            params: Dictionary or Pydantic model containing task parameters.
            wait: Whether to wait for the task to complete.
            callback: Optional async callback for status updates.
            polling_interval: Interval in seconds for status checks (default 15).
            **kwargs: Additional arguments passed to the API client.

        Returns:
            KlingStatusResponse: Final status of the task.
        """
        return await self._generate_video_internal(
            endpoint="/v1/videos/image2video",
            params_model=KlingImageToVideoParams,
            params=params,
            wait=wait,
            callback=callback,
            polling_interval=polling_interval,
            **kwargs
        )

    async def multi_image_to_video(
        self, 
        params: Union[Dict[str, Any], KlingMultiImageToVideoParams],
        wait: bool = True,
        callback: Optional[Callable] = None,
        polling_interval: int = 15,
        **kwargs
    ) -> KlingStatusResponse:
        """
        Multi-image reference video generation.

        Args:
            params: Dictionary or Pydantic model containing task parameters.
            wait: Whether to wait for the task to complete.
            callback: Optional async callback for status updates.
            polling_interval: Interval in seconds for status checks (default 15).
            **kwargs: Additional arguments passed to the API client.

        Returns:
            KlingStatusResponse: Final status of the task.
        """
        return await self._generate_video_internal(
            endpoint="/v1/videos/multi-image2video",
            params_model=KlingMultiImageToVideoParams,
            params=params,
            wait=wait,
            callback=callback,
            polling_interval=polling_interval,
            **kwargs
        )

    # --- Internal Helper ---

    async def _generate_video_internal(
        self, 
        endpoint: str, 
        params_model: Any,
        params: Union[Dict, Any],
        wait: bool,
        callback: Optional[Callable],
        polling_interval: int,
        **kwargs
    ) -> KlingStatusResponse:
        """Shared logic for task submission and optional polling"""
        request = params_model(**params) if isinstance(params, dict) else params
        request_data = request.model_dump(exclude_none=True)
        
        logger.info(f"Kling: Submitting task to {endpoint}")
        
        data = await self._request("POST", endpoint, json=request_data, **kwargs)
        init_resp = KlingStatusResponse(**data)
        
        if init_resp.code != 0:
            raise Exception(f"Kling API Error ({init_resp.code}): {init_resp.message}")
            
        task_id = init_resp.data.task_id
        
        if not wait:
            return init_resp

        return await self.poll_task(
            task_id=task_id,
            get_status_func=self.get_video_task,
            check_success_func=lambda resp: resp.is_succeeded,
            check_failed_func=lambda resp: resp.is_finished and not resp.is_succeeded,
            callback=callback,
            timeout=2400,
            interval=polling_interval
        )

def create_kling_client(ak: Optional[str] = None, sk: Optional[str] = None, base_url: Optional[str] = None) -> KlingClient:
    """Factory for KlingClient"""
    return KlingClient(ak=ak, sk=sk, base_url=base_url)

