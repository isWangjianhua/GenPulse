import asyncio
from loguru import logger
import os
from typing import Optional, Dict, Any, Union, Callable
import dashscope
from dashscope import ImageSynthesis, MultiModalConversation, VideoSynthesis
from genpulse.clients.base import BaseClient
from .schemas import (
    DashScopeImageParams,
    DashScopeImageEditParams,
    DashScopeVideoParams,
    DashScopeStatusResponse
)


class DashScopeClient(BaseClient):
    """
    DashScope (Aliyun Bailian) Service Client
    Supports multi-region base_url and automatic polling.
    """

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key or os.getenv('DASHSCOPE_API_KEY')
        if not self.api_key:
            raise ValueError("DashScope API Key is missing.")
        
        dashscope.api_key = self.api_key
        # Default: https://dashscope.aliyuncs.com/api/v1
        # International: https://dashscope-intl.aliyuncs.com/api/v1
        if base_url:
            dashscope.base_http_api_url = base_url
            logger.info(f"DashScope: Using custom base_url: {base_url}")

    async def get_task_status(self, task_id: str) -> DashScopeStatusResponse:
        """Fetch the current status of the synthesis task"""
        # SDK allows fetching by task_id or the original response object
        response = await asyncio.to_thread(
            ImageSynthesis.fetch,
            task=task_id
        )
        
        # Normalize SDK response to dict
        data = response.to_dict() if hasattr(response, 'to_dict') else response
        output = data.get("output", {})
        task_status = output.get("task_status", "UNKNOWN")
        
        # Results extraction
        results = []
        if task_status == "SUCCEEDED":
            raw_results = output.get("results", [])
            results = [{"url": r.get("url")} for r in raw_results]

        return DashScopeStatusResponse(
            task_id=task_id,
            task_status=task_status,
            results=results,
            usage=data.get("usage"),
            message=data.get("message"),
            code=data.get("code")
        )

    async def generate_image(
        self, 
        params: Union[Dict[str, Any], DashScopeImageParams],
        wait: bool = True,
        callback: Optional[Callable] = None
    ) -> DashScopeStatusResponse:
        """
        Submits an image generation task and optionally polls for completion.
        """
        # 1. Prepare request
        request = DashScopeImageParams(**params) if isinstance(params, dict) else params
        request_data = request.model_dump(exclude_none=True)
        
        # Extract core fields for SDK call
        model = request_data.pop("model")
        prompt = request_data.pop("prompt")
        
        logger.info(f"DashScope: Submitting task for {model}...")
        
        # 2. Async Submission
        response = await asyncio.to_thread(
            ImageSynthesis.async_call,
            model=model,
            prompt=prompt,
            **request_data
        )
        
        if response.status_code != 200:
            logger.error(f"DashScope: Submission failed: {response.message}")
            # If failed immediately, return a dummy response with error info
            return DashScopeStatusResponse(
                task_id="failed",
                task_status="FAILED",
                message=response.message,
                code=response.code
            )
            
        task_id = response.output.task_id
        logger.info(f"DashScope: Task created successfully. ID: {task_id}")
        
        if not wait:
            return DashScopeStatusResponse(task_id=task_id, task_status="PENDING")

        # 3. Leverage BaseClient's generic polling
        return await self.poll_task(
            task_id=task_id,
            get_status_func=self.get_task_status,
            check_success_func=lambda resp: resp.is_succeeded,
            check_failed_func=lambda resp: resp.is_finished and not resp.is_succeeded,
            callback=callback,
            timeout=600,
            interval=5 # 5 seconds as recommended by Aliyun
        )

    async def edit_image(
        self, 
        params: Union[Dict[str, Any], DashScopeImageEditParams]
    ) -> DashScopeStatusResponse:
        """
        DashScope Image Editing (Synchronous Call via MultiModalConversation)
        Useful for qwen-image-edit-max and qwen-image-edit-plus models.
        """
        # 1. Prepare request
        request = DashScopeImageEditParams(**params) if isinstance(params, dict) else params
        request_data = request.model_dump(exclude_none=True)
        
        model = request_data.pop("model")
        
        logger.info(f"DashScope: Submitting image edit request for {model}...")
        
        # 2. Synchronous Call (wrapped in thread)
        response = await asyncio.to_thread(
            MultiModalConversation.call,
            api_key=self.api_key,
            model=model,
            stream=False,
            **request_data
        )
        
        # 3. Map Response
        data = response.to_dict() if hasattr(response, 'to_dict') else response
        
        if response.status_code != 200:
            logger.error(f"DashScope: Image edit failed: {response.message}")
            return DashScopeStatusResponse(
                task_status="FAILED",
                message=response.message,
                code=response.code
            )

        # Extract results from choices
        results = []
        try:
            # MultiModalConversation output structure: output.choices[0].message.content[i].image
            choices = data.get("output", {}).get("choices", [])
            if choices:
                content_list = choices[0].get("message", {}).get("content", [])
                for item in content_list:
                    if "image" in item:
                        results.append({"url": item["image"]})
        except Exception as e:
            logger.error(f"DashScope: Error parsing image edit results: {e}")

        return DashScopeStatusResponse(
            task_status="SUCCEEDED",
            results=results,
            usage=data.get("usage")
        )

    async def get_video_task_status(self, task_id: str) -> DashScopeStatusResponse:
        """Fetch the current status of the video synthesis task"""
        response = await asyncio.to_thread(
            VideoSynthesis.fetch,
            task=task_id
        )
        data = response.to_dict() if hasattr(response, 'to_dict') else response
        output = data.get("output", {})
        task_status = output.get("task_status", "UNKNOWN")
        
        return DashScopeStatusResponse(
            task_id=task_id,
            task_status=task_status,
            video_url=output.get("video_url"),
            usage=data.get("usage"),
            message=data.get("message"),
            code=data.get("code")
        )

    async def generate_video(
        self, 
        params: Union[Dict[str, Any], DashScopeVideoParams],
        wait: bool = True,
        callback: Optional[Callable] = None
    ) -> DashScopeStatusResponse:
        """
        Submits a video generation task and optionally polls for completion.
        Supports first_frame_url and last_frame_url.
        """
        # 1. Prepare request
        request = DashScopeVideoParams(**params) if isinstance(params, dict) else params
        request_data = request.model_dump(exclude_none=True)
        
        logger.info(f"DashScope: Submitting video task for {request_data.get('model')}...")
        
        # 2. Async Submission
        response = await asyncio.to_thread(
            VideoSynthesis.async_call,
            api_key=self.api_key,
            **request_data
        )
        
        if response.status_code != 200:
            logger.error(f"DashScope: Video submission failed: {response.message}")
            return DashScopeStatusResponse(
                task_status="FAILED",
                message=response.message,
                code=response.code
            )
            
        task_id = response.output.task_id
        logger.info(f"DashScope: Video task created. ID: {task_id}")
        
        if not wait:
            return DashScopeStatusResponse(task_id=task_id, task_status="PENDING")

        # 3. Leverage BaseClient's generic polling
        return await self.poll_task(
            task_id=task_id,
            get_status_func=self.get_video_task_status,
            check_success_func=lambda resp: resp.is_succeeded,
            check_failed_func=lambda resp: resp.is_finished and not resp.is_succeeded,
            callback=callback,
            timeout=1200, # Video generation takes longer
            interval=10
        )

def create_dashscope_client(api_key: Optional[str] = None, base_url: Optional[str] = None) -> DashScopeClient:
    """Factory function for DashScopeClient"""
    return DashScopeClient(api_key=api_key, base_url=base_url)

