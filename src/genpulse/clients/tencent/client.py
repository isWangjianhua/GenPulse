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
        region: str = "ap-guangzhou",
        endpoint: str = "vod.tencentcloudapi.com",
        sub_app_id: Optional[int] = None
    ):
        super().__init__(base_url=f"https://{endpoint}")
        
        sid = secret_id or os.getenv("TENCENTCLOUD_SECRET_ID")
        skey = secret_key or os.getenv("TENCENTCLOUD_SECRET_KEY")
        self.sub_app_id = sub_app_id or (int(os.getenv("TENCENTCLOUD_SUBAPP_ID")) if os.getenv("TENCENTCLOUD_SUBAPP_ID") else None)
        
        if not sid or not skey:
            raise ValueError("Tencent Cloud SecretId and SecretKey are required.")
            
        cred = credential.Credential(sid, skey)
        http_profile = HttpProfile()
        http_profile.endpoint = endpoint
        
        client_profile = ClientProfile()
        client_profile.http_profile = http_profile
        
        self.client = vod_client.VodClient(cred, region, client_profile)

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
        callback: Optional[Callable] = None
    ) -> TencentTaskDetailResponse:
        """
        Create an AIGC video task and optionally poll for completion.
        """
        request = TencentVideoParams(**params) if isinstance(params, dict) else params
        request.SubAppId = request.SubAppId or self.sub_app_id
        request_data = request.model_dump(exclude_none=True)
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
            interval=15
        )

    async def generate_image(
        self, 
        params: Union[Dict[str, Any], TencentImageParams],
        wait: bool = True,
        callback: Optional[Callable] = None
    ) -> TencentTaskDetailResponse:
        """
        Create an AIGC image task and optionally poll for completion.
        Supports both Gemini (GEM), Qwen, and Hunyuan models.
        """
        request = TencentImageParams(**params) if isinstance(params, dict) else params
        request.SubAppId = request.SubAppId or self.sub_app_id
        request_data = request.model_dump(exclude_none=True)
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
            interval=10
        )

def create_tencent_vod_client(
    secret_id: Optional[str] = None, 
    secret_key: Optional[str] = None, 
    region: str = "ap-guangzhou"
) -> TencentVodClient:
    """Factory function for TencentVodClient"""
    return TencentVodClient(secret_id=secret_id, secret_key=secret_key, region=region)

