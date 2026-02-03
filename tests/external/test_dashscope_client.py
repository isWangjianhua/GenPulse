import asyncio
import os
import pytest
from loguru import logger
from genpulse.clients.dashscope.client import create_dashscope_client
from genpulse.clients.dashscope.schemas import DashScopeImageParams, DashScopeVideoParams

# Ensure you have set the API key before running:
# export DASHSCOPE_API_KEY="your_api_key"

@pytest.mark.asyncio
async def test_dashscope_image_generation_lifecycle():
    """
    Test the full lifecycle of a DashScope Image Generation Task:
    1. Create task
    2. Poll for completion
    3. Verify result
    """
    
    # 1. Initialize Client
    client = create_dashscope_client()
    
    # 2. Prepare Parameters
    params = DashScopeImageParams(
        model="qwen-image-plus",
        prompt="A beautiful cherry blossom tree in spring, anime style, high quality",
        n=1,
        size="1024*1024",
        style="<auto>"
    )
    
    logger.info("Step 1: Creating DashScope Image Generation Task...")
    
    try:
        # 3. Generate Image (wait=False to test manual status check first)
        response = await client.generate_image(params, wait=False)
        
        task_id = response.task_id
        logger.info(f"Task Created! ID: {task_id}")
        assert task_id is not None
        assert response.task_status in ["PENDING", "RUNNING"]
        
        # 4. Test Status Check
        logger.info("Step 2: Checking task status...")
        status_resp = await client.get_task_status(task_id)
        
        logger.info(f"Current Status: {status_resp.task_status}")
        assert status_resp.task_id == task_id
        
        # 5. Test Polling (wait=True)
        logger.info("Step 3: Polling for completion (this may take 10-30s)...")
        final_resp = await client.generate_image(params, wait=True)
        
        logger.info(f"Final Status: {final_resp.task_status}")
        
        if final_resp.is_succeeded:
            # Get image URL from results
            url = None
            if final_resp.results and len(final_resp.results) > 0:
                url = final_resp.results[0].url
            
            logger.success(f"Task Succeeded! Result URL: {url}")
            assert url is not None
            assert url.startswith("http")
        else:
            logger.error(f"Task Failed. Status: {final_resp.task_status}")
            logger.error(f"Error Message: {final_resp.message}")
            
    except Exception as e:
        logger.exception(f"Test failed with error: {e}")
        pytest.fail(f"API Call failed: {e}")


@pytest.mark.asyncio
async def test_dashscope_video_generation_lifecycle():
    """
    Test the full lifecycle of a DashScope Video Generation Task:
    1. Create task
    2. Poll for completion
    3. Verify result
    """
    
    # 1. Initialize Client
    client = create_dashscope_client()
    
    # 2. Prepare Parameters
    params = DashScopeVideoParams(
        model="wan2.2-t2v-plus",
        prompt="A cat walking on the beach at sunset, cinematic, 4k",
        size="1280*720"
    )
    
    logger.info("Step 1: Creating DashScope Video Generation Task...")
    
    try:
        # 3. Generate Video (wait=False to test manual status check)
        response = await client.generate_video(params, wait=False)
        
        task_id = response.task_id
        logger.info(f"Task Created! ID: {task_id}")
        assert task_id is not None
        assert response.task_status in ["PENDING", "RUNNING"]
        
        # 4. Test Status Check
        logger.info("Step 2: Checking task status...")
        status_resp = await client.get_task_status(task_id)
        
        logger.info(f"Current Status: {status_resp.task_status}")
        assert status_resp.task_id == task_id
        
        # 5. Test Polling (wait=True)
        logger.info("Step 3: Polling for completion (this may take 1-3 minutes)...")
        final_resp = await client.generate_video(params, wait=True)
        
        logger.info(f"Final Status: {final_resp.task_status}")
        
        if final_resp.is_succeeded:
            url = final_resp.video_url
            logger.success(f"Task Succeeded! Result URL: {url}")
            assert url is not None
            assert url.startswith("http")
        else:
            logger.error(f"Task Failed. Status: {final_resp.task_status}")
            logger.error(f"Error Message: {final_resp.message}")
            
    except Exception as e:
        logger.exception(f"Test failed with error: {e}")
        pytest.fail(f"API Call failed: {e}")


if __name__ == "__main__":
    # Integration test entry point
    async def run_all():
        await test_dashscope_image_generation_lifecycle()
        await test_dashscope_video_generation_lifecycle()
    
    asyncio.run(run_all())
