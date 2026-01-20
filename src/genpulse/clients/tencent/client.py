import asyncio
import logging
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
    TencentStatusResponse,
    TencentVideoResponse,
    TencentImageParams,
    TencentImageStatusResponse
)

logger = logging.getLogger("TencentVodClient")

class TencentVodClient(BaseClient):
    """
    Tencent Cloud VOD AIGC Video Client.
    Uses official SDK wrapped in asyncio.to_thread for async execution.
    """

    def __init__(
        self, 
        secret_id: Optional[str] = None, 
        secret_key: Optional[str] = None, 
        region: str = "ap-guangzhou",
        endpoint: str = "vod.tencentcloudapi.com"
    ):
        super().__init__(base_url=f"https://{endpoint}")
        
        sid = secret_id or os.getenv("TENCENTCLOUD_SECRET_ID")
        skey = secret_key or os.getenv("TENCENTCLOUD_SECRET_KEY")
        
        if not sid or not skey:
            raise ValueError("Tencent Cloud SecretId and SecretKey are required.")
            
        cred = credential.Credential(sid, skey)
        http_profile = HttpProfile()
        http_profile.endpoint = endpoint
        
        client_profile = ClientProfile()
        client_profile.http_profile = http_profile
        
        self.client = vod_client.VodClient(cred, region, client_profile)

    async def get_video_task(self, task_id: str) -> TencentStatusResponse:
        """Query the status of an AIGC video task"""
        logger.info(f"Tencent: Querying task {task_id}")
        
        req = models.DescribeAigcVideoTaskRequest()
        req.TaskId = task_id
        
        resp = await asyncio.to_thread(self.client.DescribeAigcVideoTask, req)
        data = json.loads(resp.to_json_string())
        
        return TencentStatusResponse(**data)

    async def generate_video(
        self, 
        params: Union[Dict[str, Any], TencentVideoParams],
        wait: bool = True,
        callback: Optional[Callable] = None
    ) -> TencentStatusResponse:
        """
        Create an AIGC video task and optionally poll for completion.
        """
        request = TencentVideoParams(**params) if isinstance(params, dict) else params
        request_data = request.model_dump(exclude_none=True)
        
        logger.info(f"Tencent: Creating AIGC video task (Type: {request.Type})")
        
        req = models.CreateAigcVideoTaskRequest()
        req.from_json_string(json.dumps(request_data))
        
        resp = await asyncio.to_thread(self.client.CreateAigcVideoTask, req)
        data = json.loads(resp.to_json_string())
        
        init_resp = TencentVideoResponse(**data)
        task_id = init_resp.TaskId
        logger.info(f"Tencent: Task created. ID: {task_id}")
        
        if not wait:
            # Return a partial status response
            return TencentStatusResponse(
                TaskId=task_id,
                Status="WAIT",
                RequestId=init_resp.RequestId
            )

        # Polling via BaseClient
        return await self.poll_task(
            task_id=task_id,
            get_status_func=self.get_video_task,
            check_success_func=lambda resp: resp.is_succeeded,
            check_failed_func=lambda resp: resp.is_finished and not resp.is_succeeded,
            callback=callback,
            timeout=1800,
            interval=15
        )

    async def get_image_task(self, task_id: str) -> TencentImageStatusResponse:
        """Query the status of an AIGC image task"""
        logger.info(f"Tencent: Querying image task {task_id}")
        
        req = models.DescribeAigcImageTaskRequest()
        req.TaskId = task_id
        
        resp = await asyncio.to_thread(self.client.DescribeAigcImageTask, req)
        data = json.loads(resp.to_json_string())
        
        return TencentImageStatusResponse(**data)

    async def generate_image(
        self, 
        params: Union[Dict[str, Any], TencentImageParams],
        wait: bool = True,
        callback: Optional[Callable] = None
    ) -> TencentImageStatusResponse:
        """
        Create an AIGC image task and optionally poll for completion.
        Supports both Gemini (GEM), Qwen, and Hunyuan models.
        """
        request = TencentImageParams(**params) if isinstance(params, dict) else params
        request_data = request.model_dump(exclude_none=True)
        
        logger.info(f"Tencent: Creating AIGC image task (Model: {request.ModelName})")
        
        req = models.CreateAigcImageTaskRequest()
        req.from_json_string(json.dumps(request_data))
        
        resp = await asyncio.to_thread(self.client.CreateAigcImageTask, req)
        data = json.loads(resp.to_json_string())
        
        init_resp = TencentVideoResponse(**data)
        task_id = init_resp.TaskId
        
        if not wait:
            return TencentImageStatusResponse(
                TaskId=task_id,
                Status="WAIT",
                RequestId=init_resp.RequestId
            )

        # Polling via BaseClient
        return await self.poll_task(
            task_id=task_id,
            get_status_func=self.get_image_task,
            check_success_func=lambda resp: resp.is_succeeded,
            check_failed_func=lambda resp: resp.is_finished and not resp.is_succeeded,
            callback=callback,
            timeout=600, # Image generation is usually faster
            interval=10
        )

def create_tencent_vod_client(
    secret_id: Optional[str] = None, 
    secret_key: Optional[str] = None, 
    region: str = "ap-guangzhou"
) -> TencentVodClient:
    """Factory function for TencentVodClient"""
    return TencentVodClient(secret_id=secret_id, secret_key=secret_key, region=region)

