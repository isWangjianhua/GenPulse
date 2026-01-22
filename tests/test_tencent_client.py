import asyncio
import os
import pytest
from loguru import logger
from genpulse.clients.tencent.client import create_tencent_vod_client
from genpulse.clients.tencent.schemas import TencentImageParams, TencentVideoParams

# Ensure you have set these environment variables before running
# export TENCENTCLOUD_SECRET_ID="your_id"
# export TENCENTCLOUD_SECRET_KEY="your_key"
# export TENCENTCLOUD_SUBAPP_ID="your_subapp_id" (Optional)

@pytest.mark.asyncio
async def test_tencent_image_generation_lifecycle():
    """
    Test the full lifecycle of a Tencent VOD AIGC Image Task:
    1. Create task
    2. Check status via unified method
    3. Wait for completion via polling
    """
    
    # 1. Initialize Client
    client = create_tencent_vod_client()
    
    # 2. Prepare Parameters (Using Hunyuan 3.0 for a simple prompt)
    params = TencentImageParams(
        ModelName="Hunyuan",
        ModelVersion="3.0",
        Prompt="1girl, A futuristic city with flying cars, cyberpunk style, hyper-realistic, 8k.",
        OutputConfig={
            "AspectRatio": "16:9",
            "Resolution": "1024x576"
        }
    )
    
    logger.info("Step 1: Creating AIGC Image Task...")
    
    # 3. Generate Image (wait=False to test manual status check first)
    try:
        # Initial creation
        response = await client.generate_image(params, wait=False)
        
        task_id = response.TaskId
        logger.info(f"Task Created! ID: {task_id}")
        assert task_id is not None
        assert response.Status == "WAITING"

        # 4. Test Unified Status Check
        logger.info("Step 2: Checking task status via DescribeTaskDetail...")
        status_resp = await client.get_task_status(task_id)
        
        logger.info(f"Current Status: {status_resp.Status}")
        # Only assert if TaskId is back (Tencent might omit it in raw WAITING response)
        if status_resp.TaskId:
            assert status_resp.TaskId == task_id
        assert status_resp.TaskType == "AigcImageTask"

        # 5. Test Polling (wait=True)
        logger.info("Step 3: Polling for completion (this may take 30-60s)...")
        final_resp = await client.generate_image(params, wait=True)
        
        logger.info(f"Final Status: {final_resp.Status}")
        
        if final_resp.is_succeeded:
            url = final_resp.result_url
            logger.success(f"Task Succeeded! Result URL: {url}")
            assert url is not None
            assert url.startswith("http")
        else:
            logger.error(f"Task Failed or Aborted. Status: {final_resp.Status}")
            # If failed, check internal info
            if final_resp.AigcImageTask:
                logger.error(f"Error Message: {final_resp.AigcImageTask.Message}")

    except Exception as e:
        logger.exception(f"Test failed with error: {e}")
        pytest.fail(f"API Call failed: {e}")

@pytest.mark.asyncio
async def test_tencent_video_generation_lifecycle():
    """
    Test the full lifecycle of a Tencent VOD AIGC Video Task:
    1. Create task
    2. Check status via unified method
    3. Wait for completion via polling
    """
    
    # 1. Initialize Client
    client = create_tencent_vod_client()
    
    # 2. Prepare Parameters (Using Hunyuan for a simple prompt)
    params = TencentVideoParams(
        ModelName="Hunyuan",
        ModelVersion="1.5",
        Prompt="A beautiful sunset over the mountains, cinematic style, 4k",
        OutputConfig={
            "AspectRatio": "16:9",
            "Resolution": "720P"
        }
    )
    
    logger.info("Step 1: Creating AIGC Video Task...")
    
    # 3. Generate Video (wait=False to test manual status check first)
    try:
        # Initial creation
        response = await client.generate_video(params, wait=False)
        
        task_id = response.TaskId
        logger.info(f"Task Created! ID: {task_id}")
        assert task_id is not None
        assert response.Status == "WAITING"

        # 4. Test Unified Status Check
        logger.info("Step 2: Checking task status via DescribeTaskDetail...")
        status_resp = await client.get_task_status(task_id)
        
        logger.info(f"Current Status: {status_resp.Status}")
        if status_resp.TaskId:
            assert status_resp.TaskId == task_id
        assert status_resp.TaskType == "AigcVideoTask"

        # 5. Test Polling (wait=True)
        logger.info("Step 3: Polling for completion (this may take 1-5 minutes)...")
        final_resp = await client.generate_video(params, wait=True)
        
        logger.info(f"Final Status: {final_resp.Status}")
        
        if final_resp.is_succeeded:
            url = final_resp.result_url
            logger.success(f"Task Succeeded! Result URL: {url}")
            assert url is not None
            assert url.startswith("http")
        else:
            logger.error(f"Task Failed or Aborted. Status: {final_resp.Status}")
            if final_resp.AigcVideoTask:
                logger.error(f"Error Message: {final_resp.AigcVideoTask.Message}")

    except Exception as e:
        logger.exception(f"Test failed with error: {e}")
        pytest.fail(f"API Call failed: {e}")

if __name__ == "__main__":
    # Integration test entry point
    async def run_all():
        await test_tencent_image_generation_lifecycle()
        await test_tencent_video_generation_lifecycle()
    
    asyncio.run(run_all())
