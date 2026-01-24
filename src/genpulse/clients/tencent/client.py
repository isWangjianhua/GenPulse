import asyncio
from loguru import logger
import os
import json
from typing import Optional, Dict, Any, Union, Callable
from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.vod.v20180717 import vod_client, models

from genpulse.clients.base import BaseClient
from .schemas import (
    TencentVideoParams,
    TencentTaskResponse,
    TencentImageParams,
    TencentTaskDetailResponse
)


class TencentVodClient(BaseClient):
    """
    Tencent Cloud VOD AIGC Video Client.
    Uses official SDK wrapped in asyncio.to_thread for async execution.
    """

    def __init__(
        self, 
        secret_id: Optional[str] = None, 
        secret_key: Optional[str] = None, 
        sub_app_id: Optional[str] = None,
        endpoint: Optional[str] = None,
        region: Optional[str] = None
    ):
        # BaseClient expectation regarding base_url might be informational
        self.endpoint_val = endpoint or "vod.tencentcloudapi.com"
        super().__init__(base_url=f"https://{self.endpoint_val}")
        
        self.secret_id = secret_id or os.getenv("TENCENTCLOUD_SECRET_ID")
        self.secret_key = secret_key or os.getenv("TENCENTCLOUD_SECRET_KEY")
        
        # Parse SubAppId
        sub_app_id_val = sub_app_id or os.getenv("TENCENTCLOUD_SUBAPP_ID")
        self.sub_app_id = int(sub_app_id_val) if sub_app_id_val else None
        
        self.region = region or os.getenv("TENCENTCLOUD_REGION", "ap-guangzhou")
        
        if not self.secret_id or not self.secret_key:
            raise ValueError("Tencent Cloud SecretId and SecretKey are required.")
            
        cred = credential.Credential(self.secret_id, self.secret_key)
        http_profile = HttpProfile()
        http_profile.endpoint = self.endpoint_val
        
        client_profile = ClientProfile()
        client_profile.http_profile = http_profile
        
        self.client = vod_client.VodClient(cred, self.region, client_profile)

    async def get_task_status(self, task_id: str, sub_app_id: Optional[int] = None) -> TencentTaskDetailResponse:
        """
        Unified status check for any VOD task using DescribeTaskDetail.
        Replaces the need for specific DescribeAigcVideoTask/DescribeAigcImageTask calls.
        """
        logger.info(f"Tencent: Querying task status for {task_id}")
        req = models.DescribeTaskDetailRequest()
        req.TaskId = task_id
        req.SubAppId = sub_app_id or self.sub_app_id
        
        resp = await asyncio.to_thread(self.client.DescribeTaskDetail, req)
        data = json.loads(resp.to_json_string())
        return TencentTaskDetailResponse(**data)

    async def generate_video(
        self, 
        params: Union[Dict[str, Any], TencentVideoParams],
        wait: bool = True,
        callback: Optional[Callable] = None,
        polling_interval: int = 15,
        **kwargs
    ) -> TencentTaskDetailResponse:
        """
        Create an AIGC video task and optionally poll for completion.

        Args:
            params: Dictionary or Pydantic model containing task parameters.
            wait: Whether to wait for the task to complete.
            callback: Optional async callback for status updates.
            polling_interval: Interval in seconds for status checks (default 15).
            **kwargs: Additional parameters merged into the request.

        Returns:
            TencentTaskDetailResponse: Final status and details of the task.
        """
        request = TencentVideoParams(**params) if isinstance(params, dict) else params
        request.SubAppId = request.SubAppId or self.sub_app_id
        
        request_data = request.model_dump(exclude_none=True)
        # Merge additional kwargs into request_data
        request_data.update(kwargs)

        logger.info(f"Tencent: Creating AIGC video task (Model: {request.ModelName})")
        req = models.CreateAigcVideoTaskRequest()
        req.from_json_string(json.dumps(request_data))
        
        resp = await asyncio.to_thread(self.client.CreateAigcVideoTask, req)
        data = json.loads(resp.to_json_string())
        init_resp = TencentTaskResponse(**data)
        task_id = init_resp.TaskId
        logger.info(f"Tencent: Task created. ID: {task_id}; Data: {data}")
        
        if not wait:
            # Return a partial status response
            return TencentTaskDetailResponse(
                TaskId=task_id,
                TaskType="AigcVideoTask",
                Status="WAITING",
                CreateTime="", # Not available without polling
                RequestId=init_resp.RequestId
            )

        # Polling via BaseClient
        return await self.poll_task(
            task_id=task_id,
            get_status_func=lambda tid: self.get_task_status(tid, sub_app_id=request.SubAppId or self.sub_app_id),
            check_success_func=lambda resp: resp.is_succeeded,
            check_failed_func=lambda resp: resp.is_finished and not resp.is_succeeded,
            callback=callback,
            timeout=1800,
            interval=polling_interval
        )

    async def generate_image(
        self, 
        params: Union[Dict[str, Any], TencentImageParams],
        wait: bool = True,
        callback: Optional[Callable] = None,
        polling_interval: int = 5,
        **kwargs
    ) -> TencentTaskDetailResponse:
        """
        Create an AIGC image task and optionally poll for completion.
        Supports both Gemini (GEM), Qwen, and Hunyuan models.

        Args:
            params: Dictionary or Pydantic model containing task parameters.
            wait: Whether to wait for the task to complete.
            callback: Optional async callback for status updates.
            polling_interval: Interval in seconds for status checks (default 5).
            **kwargs: Additional parameters merged into the request.

        Returns:
            TencentTaskDetailResponse: Final status and details of the task.
        """
        request = TencentImageParams(**params) if isinstance(params, dict) else params
        request.SubAppId = request.SubAppId or self.sub_app_id
        
        request_data = request.model_dump(exclude_none=True)
        # Merge additional kwargs into request_data
        request_data.update(kwargs)

        logger.info(f"Tencent: Creating AIGC image task (Model: {request.ModelName})")
        req = models.CreateAigcImageTaskRequest()
        req.from_json_string(json.dumps(request_data))
        
        resp = await asyncio.to_thread(self.client.CreateAigcImageTask, req)
        data = json.loads(resp.to_json_string())
        init_resp = TencentTaskResponse(**data)
        task_id = init_resp.TaskId
        logger.info(f"Tencent: Task created. ID: {task_id}; Data: {data}")
        
        if not wait:
            return TencentTaskDetailResponse(
                TaskId=task_id,
                TaskType="AigcImageTask",
                Status="WAITING",
                CreateTime="",
                RequestId=init_resp.RequestId
            )

        # Polling via BaseClient
        return await self.poll_task(
            task_id=task_id,
            get_status_func=lambda tid: self.get_task_status(tid, sub_app_id=request.SubAppId or self.sub_app_id),
            check_success_func=lambda resp: resp.is_succeeded,
            check_failed_func=lambda resp: resp.is_finished and not resp.is_succeeded,
            callback=callback,
            timeout=600, # Image generation is usually faster
            interval=polling_interval
        )

def create_tencent_vod_client(
    secret_id: Optional[str] = None, 
    secret_key: Optional[str] = None, 
    sub_app_id: Optional[str] = None,
    endpoint: Optional[str] = None,
    region: Optional[str] = None
) -> TencentVodClient:
    """Factory function for TencentVodClient"""
    return TencentVodClient(
        secret_id=secret_id, 
        secret_key=secret_key, 
        sub_app_id=sub_app_id,
        endpoint=endpoint,
        region=region
    )

