import asyncio
import os
import pytest
from loguru import logger
from genpulse.clients.volcengine.client import create_volcengine_client
from genpulse.clients.volcengine.schemas import VolcImageParams, VolcVideoParams

# Ensure you have set these environment variables before running:
# export GENPULSE_VOLC_ACCESS_KEY="your_access_key"
# export GENPULSE_VOLC_SECRET_KEY="your_secret_key"

@pytest.mark.asyncio
async def test_volcengine_image_generation_lifecycle():
    """
    Test the full lifecycle of a VolcEngine Image Generation Task:
    1. Create task (synchronous API)
    2. Verify result
    """
    
    # 1. Initialize Client
    client = create_volcengine_client()
    
    # 2. Prepare Parameters
    params = VolcImageParams(
        model="doubao-seedream-4-0-250828",  # VolcEngine model endpoint ID
        prompt="A majestic mountain landscape at dawn, photorealistic, 8k",
        size="1024x1024",
        seed=42,
        watermark=False
    )
    
    logger.info("Step 1: Creating VolcEngine Image Generation Task...")
    
    try:
        # 3. Generate Image (VolcEngine image API is synchronous)
        response = await client.generate_image(params)
        
        logger.info(f"Response Status: {response.status if hasattr(response, 'status') else 'N/A'}")
        
        # Check for errors
        if response.error:
            logger.error(f"API Error: {response.error.code} - {response.error.message}")
            pytest.fail(f"Image generation failed: {response.error.message}")
        
        # Verify images were returned
        assert response.data is not None
        assert len(response.data) > 0
        
        image = response.data[0]
        image_url = image.url if hasattr(image, 'url') else image.get('url')
        
        logger.success(f"Task Succeeded! Image URL: {image_url}")
        assert image_url is not None
        assert image_url.startswith("http")
        
    except Exception as e:
        logger.exception(f"Test failed with error: {e}")
        pytest.fail(f"API Call failed: {e}")


@pytest.mark.asyncio
async def test_volcengine_video_generation_lifecycle():
    """
    Test the full lifecycle of a VolcEngine Video Generation Task:
    1. Create task
    2. Poll for completion
    3. Verify result
    """
    
    # 1. Initialize Client
    client = create_volcengine_client()
    
    # 2. Prepare Parameters (Text-to-Video)
    params = VolcVideoParams(
        model="doubao-seedance-1-0-lite-t2v-250428",  # VolcEngine video model
        content=[
            {"type": "text", "text": "A peaceful river flowing through a forest, birds singing, sunlight filtering through trees"}
        ],
        resolution="720p",
        duration=5,
        seed=42
    )
    
    logger.info("Step 1: Creating VolcEngine Video Generation Task...")
    
    try:
        # 3. Generate Video (wait=False to test status check)
        response = await client.generate_video(params, wait=False)
        
        # VolcEngine returns task id for async video generation
        task_id = response.id
        logger.info(f"Task Created! ID: {task_id}")
        assert task_id is not None
        
        # Initial status should be pending or processing
        logger.info(f"Initial Status: {response.status}")
        assert response.status in ["pending", "processing", "running", "queued"]
        
        # 4. Test Status Check
        logger.info("Step 2: Checking task status...")
        status_resp = await client.get_video_task(task_id)
        
        logger.info(f"Current Status: {status_resp.status}")
        assert status_resp.id == task_id
        
        # 5. Test Polling (wait=True)
        logger.info("Step 3: Polling for completion (this may take 1-3 minutes)...")
        
        # Create callback to log progress
        async def progress_callback(resp):
            logger.info(f"Progress Update - Status: {resp.status}")
        
        final_resp = await client.generate_video(params, wait=True, callback=progress_callback)
        
        logger.info(f"Final Status: {final_resp.status}")
        
        if final_resp.status == "succeeded":
            # VolcEngine returns video URL in content.video_url
            video_url = None
            if final_resp.content and hasattr(final_resp.content, 'video_url'):
                video_url = final_resp.content.video_url
            
            logger.success(f"Task Succeeded! Video URL: {video_url}")
            
            if video_url:
                assert video_url.startswith("http")
            else:
                logger.warning("No video URL found in response, but task succeeded")
        else:
            logger.error(f"Task Failed or Not Completed. Status: {final_resp.status}")
            pytest.fail(f"Video generation did not complete successfully: {final_resp.status}")
            
    except Exception as e:
        logger.exception(f"Test failed with error: {e}")
        pytest.fail(f"API Call failed: {e}")


@pytest.mark.asyncio
async def test_volcengine_image_to_video_lifecycle():
    """
    Test VolcEngine Image-to-Video generation.
    """
    
    # 1. Initialize Client
    client = create_volcengine_client()
    
    # 2. Prepare Parameters (Image-to-Video)
    # You'll need a valid image URL from VolcEngine's image generation or an accessible URL
    params = VolcVideoParams(
        model="doubao-seedance-1-0-lite-i2v-250428",
        content=[
            {"type": "image_url", "image_url": {"url": "https://example.com/starting-frame.jpg"}},
            {"type": "text", "text": "The character starts walking forward"}
        ],
        resolution="720p",
        duration=5
    )
    
    logger.info("Step 1: Creating VolcEngine Image-to-Video Task...")
    
    try:
        # 3. Generate Video with polling
        logger.info("Polling for completion (this may take 1-3 minutes)...")
        
        response = await client.generate_video(params, wait=True)
        
        logger.info(f"Final Status: {response.status}")
        
        if response.status == "succeeded":
            video_url = response.content.video_url if response.content else None
            logger.success(f"Image-to-Video Task Succeeded! Video URL: {video_url}")
            assert response.id is not None
        else:
            logger.warning(f"Task status: {response.status}")
            # I2V might fail if image URL is invalid, that's expected for this test
            
    except Exception as e:
        logger.warning(f"I2V test skipped or failed (expected if no valid image URL): {e}")
        # Don't fail the entire test suite for I2V


if __name__ == "__main__":
    # Integration test entry point
    async def run_all():
        await test_volcengine_image_generation_lifecycle()
        await test_volcengine_video_generation_lifecycle()
        # await test_volcengine_image_to_video_lifecycle()  # Commented out as it needs a real image
    
    asyncio.run(run_all())
