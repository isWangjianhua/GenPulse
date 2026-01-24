import asyncio
from loguru import logger
import os
import time
import datetime
import httpx
from typing import Optional, Dict, Any, Union, Callable
from baidubce.auth import bce_v1_signer
from baidubce.http import http_methods, bce_http_client
from baidubce.http import http_headers

from genpulse.clients.base import BaseClient
from .schemas import (
    BaiduTextToVideoParams,
    BaiduImageToVideoParams,
    BaiduVideoExtendParams,
    BaiduLipSyncParams,
    BaiduTextToImageParams,
    BaiduImageToImageParams,
    BaiduLargeModelImageParams,
    BaiduVideoToVideoParams,
    BaiduTaskListParams,
    BaiduTaskListResponse,
    BaiduAigcResponse,
    BaiduStatusResponse
)


class BaiduVodClient(BaseClient):
    """
    Baidu Cloud VOD AIGC Video Client.
    Implements BCE-AUTH-V1 signature for REST API calls.
    """

    def __init__(
        self, 
        ak: Optional[str] = None, 
        sk: Optional[str] = None, 
        endpoint: Optional[str] = None
    ):
        # Default endpoint: vod.baidubce.com
        self.host = endpoint or "vod.baidubce.com"
        super().__init__(base_url=f"https://{self.host}")
        
        self.ak = ak or os.getenv('BAIDU_AK')
        self.sk = sk or os.getenv('BAIDU_SK')
        
        if not self.ak or not self.sk:
            raise ValueError("Baidu AK and SK are required for authentication.")

    def _get_auth_header(self, method: str, path: str, params: Dict[str, str], headers: Dict[str, str]) -> str:
        """Generate BCE-AUTH-V1 signature"""
        timestamp = int(time.time())
        # Baidu SDK expects a credentials object or similar, but we can use the signer directly
        # Format: bce-auth-v1/{accessKeyId}/{timestamp}/{expirationPeriodInSeconds}/{signedHeaders}/{signature}
        
        # We'll use a simplified version of signing or the SDK signer if easy
        # Actually, manually creating the canonical request is better for async httpx
        return bce_v1_signer.sign(self.ak, self.sk, method, path, headers, params)

    async def _request(self, method: str, path: str, **kwargs) -> Dict[str, Any]:
        """Override _request to include Baidu BCE authentication"""
        headers = kwargs.get("headers", {}).copy()
        headers["Host"] = self.host
        headers["x-bce-date"] = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
        
        query_params = kwargs.get("params", {})
        
        # Generate signature
        auth = self._get_auth_header(method, path, query_params, headers)
        headers["Authorization"] = auth
        
        kwargs["headers"] = headers
        
        return await super()._request(method, path, **kwargs)

    # --- Public Methods ---

    async def get_task(self, task_id: str) -> BaiduStatusResponse:
        """Query the status of an AIGC task (Video or Image)"""
        logger.info(f"Baidu: Querying task {task_id}")
        data = await self._request("GET", f"/v2/aigc/task/{task_id}")
        return BaiduStatusResponse(**data)

    async def list_tasks(
        self, 
        pn: int = 1, 
        ps: int = 20
    ) -> BaiduTaskListResponse:
        """Query the list of AIGC tasks"""
        logger.info(f"Baidu: Listing tasks (Page: {pn}, Size: {ps})")
        params = {"pn": pn, "ps": ps}
        data = await self._request("GET", "/v2/aigc/task", params=params)
        return BaiduTaskListResponse(**data)

    async def text_to_video(
        self, 
        params: Union[Dict[str, Any], BaiduTextToVideoParams],
        wait: bool = True,
        callback: Optional[Callable] = None,
        polling_interval: int = 15,
        **kwargs
    ) -> BaiduStatusResponse:
        """
        Submit a Text-to-Video task.

        Args:
            params: Dictionary or Pydantic model containing task parameters.
            wait: Whether to wait for the task to complete.
            callback: Optional async callback for status updates.
            polling_interval: Interval in seconds for status checks (default 15).
            **kwargs: Additional arguments passed to the API client (e.g. headers).

        Returns:
            BaiduStatusResponse: Final status of the task.
        """
        return await self._generate_aigc_internal(
            "/v2/aigc/text_to_video", 
            BaiduTextToVideoParams, 
            params, 
            wait=wait,
            callback=callback,
            polling_interval=polling_interval,
            **kwargs
        )

    async def image_to_video(
        self, 
        params: Union[Dict[str, Any], BaiduImageToVideoParams],
        wait: bool = True,
        callback: Optional[Callable] = None,
        polling_interval: int = 15,
        **kwargs
    ) -> BaiduStatusResponse:
        """
        Submit an Image-to-Video task.

        Args:
            params: Dictionary or Pydantic model containing task parameters.
            wait: Whether to wait for the task to complete.
            callback: Optional async callback for status updates.
            polling_interval: Interval in seconds for status checks (default 15).
            **kwargs: Additional arguments passed to the API client.

        Returns:
            BaiduStatusResponse: Final status of the task.
        """
        return await self._generate_aigc_internal(
            "/v2/aigc/image_to_video", 
            BaiduImageToVideoParams, 
            params, 
            wait=wait,
            callback=callback,
            polling_interval=polling_interval,
            **kwargs
        )

    async def video_extend(
        self, 
        params: Union[Dict[str, Any], BaiduVideoExtendParams],
        wait: bool = True,
        callback: Optional[Callable] = None,
        polling_interval: int = 15,
        **kwargs
    ) -> BaiduStatusResponse:
        """
        Submit a Video-Extend task.

        Args:
            params: Dictionary or Pydantic model containing task parameters.
            wait: Whether to wait for the task to complete.
            callback: Optional async callback for status updates.
            polling_interval: Interval in seconds for status checks (default 15).
            **kwargs: Additional arguments passed to the API client.

        Returns:
            BaiduStatusResponse: Final status of the task.
        """
        return await self._generate_aigc_internal(
            "/v2/aigc/video_extend", 
            BaiduVideoExtendParams, 
            params, 
            wait=wait,
            callback=callback,
            polling_interval=polling_interval,
            **kwargs
        )

    async def lip_sync(
        self, 
        params: Union[Dict[str, Any], BaiduLipSyncParams],
        wait: bool = True,
        callback: Optional[Callable] = None,
        polling_interval: int = 15,
        **kwargs
    ) -> BaiduStatusResponse:
        """
        Submit a Lip-Sync task.

        Args:
            params: Dictionary or Pydantic model containing task parameters.
            wait: Whether to wait for the task to complete.
            callback: Optional async callback for status updates.
            polling_interval: Interval in seconds for status checks (default 15).
            **kwargs: Additional arguments passed to the API client.

        Returns:
            BaiduStatusResponse: Final status of the task.
        """
        return await self._generate_aigc_internal(
            "/v2/aigc/lip_sync", 
            BaiduLipSyncParams, 
            params, 
            wait=wait,
            callback=callback,
            polling_interval=polling_interval,
            **kwargs
        )

    # --- Image Generation Methods ---

    async def text_to_image(
        self, 
        params: Union[Dict[str, Any], BaiduTextToImageParams],
        wait: bool = True,
        callback: Optional[Callable] = None,
        polling_interval: int = 5,
        **kwargs
    ) -> BaiduStatusResponse:
        """
        Submit a Text-to-Image task.

        Args:
            params: Dictionary or Pydantic model containing task parameters.
            wait: Whether to wait for the task to complete.
            callback: Optional async callback for status updates.
            polling_interval: Interval in seconds for status checks (default 5).
            **kwargs: Additional arguments passed to the API client.

        Returns:
            BaiduStatusResponse: Final status of the task.
        """
        return await self._generate_aigc_internal(
            "/v2/aigc/text_to_image", 
            BaiduTextToImageParams, 
            params, 
            wait=wait,
            callback=callback,
            polling_interval=polling_interval,
            **kwargs
        )

    async def image_to_image(
        self, 
        params: Union[Dict[str, Any], BaiduImageToImageParams],
        wait: bool = True,
        callback: Optional[Callable] = None,
        polling_interval: int = 5,
        **kwargs
    ) -> BaiduStatusResponse:
        """
        Submit an Image-to-Image task.

        Args:
            params: Dictionary or Pydantic model containing task parameters.
            wait: Whether to wait for the task to complete.
            callback: Optional async callback for status updates.
            polling_interval: Interval in seconds for status checks (default 5).
            **kwargs: Additional arguments passed to the API client.

        Returns:
            BaiduStatusResponse: Final status of the task.
        """
        return await self._generate_aigc_internal(
            "/v2/aigc/image_to_image", 
            BaiduImageToImageParams, 
            params, 
            wait=wait,
            callback=callback,
            polling_interval=polling_interval,
            **kwargs
        )

    async def create_image_task(
        self, 
        params: Union[Dict[str, Any], BaiduLargeModelImageParams],
        wait: bool = True,
        callback: Optional[Callable] = None,
        polling_interval: int = 15,
        **kwargs
    ) -> BaiduStatusResponse:
        """
        Submit a Large Model Image Generation task.

        Args:
            params: Dictionary or Pydantic model containing task parameters.
            wait: Whether to wait for the task to complete.
            callback: Optional async callback for status updates.
            polling_interval: Interval in seconds for status checks (default 15).
            **kwargs: Additional arguments passed to the API client.

        Returns:
            BaiduStatusResponse: Final status of the task.
        """
        return await self._generate_aigc_internal(
            "/v2/aigc/create_image_task", 
            BaiduLargeModelImageParams, 
            params, 
            wait=wait,
            callback=callback,
            polling_interval=polling_interval,
            **kwargs
        )

    async def video_to_video(
        self, 
        params: Union[Dict[str, Any], BaiduVideoToVideoParams],
        wait: bool = True,
        callback: Optional[Callable] = None,
        polling_interval: int = 15,
        **kwargs
    ) -> BaiduStatusResponse:
        """
        Submit a Video-to-Video generation task.

        Args:
            params: Dictionary or Pydantic model containing task parameters.
            wait: Whether to wait for the task to complete.
            callback: Optional async callback for status updates.
            polling_interval: Interval in seconds for status checks (default 15).
            **kwargs: Additional arguments passed to the API client.

        Returns:
            BaiduStatusResponse: Final status of the task.
        """
        return await self._generate_aigc_internal(
            "/v2/aigc/video_to_video", 
            BaiduVideoToVideoParams, 
            params, 
            wait=wait,
            callback=callback,
            polling_interval=polling_interval,
            **kwargs
        )

    # --- Internal Helper ---

    async def _generate_aigc_internal(
        self, 
        endpoint: str,
        params_model: Any,
        params: Union[Dict[str, Any], Any],
        wait: bool = True,
        callback: Optional[Callable] = None,
        polling_interval: int = 15,
        **kwargs
    ) -> BaiduStatusResponse:
        """Shared logic for all Baidu AIGC tasks"""
        request = params if isinstance(params, params_model) else params_model(**params)
        
        # Baidu requires inputs in a specific key based on model, e.g. "modelK25TTaskInput"
        input_key = f"model{request.model}TaskInput"
        payload = {
            "model": request.model,
            input_key: request.taskInput.model_dump(exclude_none=True)
        }
        
        logger.info(f"Baidu: Submitting task to {endpoint} (Model: {request.model})")
        # Pass kwargs (like headers, timeout) to the underlying _request
        data = await self._request("POST", endpoint, json=payload, **kwargs)
        init_resp = BaiduAigcResponse(**data)
        
        task_id = init_resp.taskId
        
        if not wait:
            return BaiduStatusResponse(taskId=task_id, status="PROCESSING")

        return await self.poll_task(
            task_id=task_id,
            get_status_func=self.get_task,
            check_success_func=lambda resp: resp.is_succeeded,
            check_failed_func=lambda resp: resp.is_finished and not resp.is_succeeded,
            callback=callback,
            timeout=1800,
            interval=polling_interval
        )

def create_baidu_vod_client(ak: Optional[str] = None, sk: Optional[str] = None, endpoint: Optional[str] = None) -> BaiduVodClient:
    """Factory function for BaiduVodClient"""
    return BaiduVodClient(ak=ak, sk=sk, endpoint=endpoint)

