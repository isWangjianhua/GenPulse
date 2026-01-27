import pytest
import asyncio
import os
from httpx import AsyncClient, ASGITransport
from loguru import logger

# This is an integration test that requires:
# 1. Real Tencent API credentials in environment
# 2. Running Redis and PostgreSQL (docker-compose up -d)
# 3. Full system stack: FastAPI + Worker + TencentClient

@pytest.mark.asyncio
@pytest.mark.integration
async def test_tencent_text_to_image_http_polling_flow():
    """
    End-to-End Integration Test: HTTP Request → MQ → Worker → Handler → TencentClient → Result
    
    This test validates the complete lifecycle:
    1. POST /task with provider="tencent"
    2. Task queued to Redis MQ
    3. Worker picks up task and routes to TextToImageHandler
    4. Handler calls TencentVodClient with polling
    5. Final result retrieved via GET /task/{task_id}
    
    Prerequisites:
    - export TENCENTCLOUD_SECRET_ID="your_id"
    - export TENCENTCLOUD_SECRET_KEY="your_key"
    - docker-compose up -d (Redis + PostgreSQL)
    """
    
    # Verify environment variables
    required_env = ["TENCENTCLOUD_SECRET_ID", "TENCENTCLOUD_SECRET_KEY"]
    for env_var in required_env:
        if not os.getenv(env_var):
            pytest.skip(f"Skipping test: {env_var} not set")
    
    from genpulse.app import create_api
    from genpulse.worker import Worker
    
    # 1. Create FastAPI app
    app = create_api()
    
    # 2. Start Worker in background
    worker = Worker()
    worker_task = asyncio.create_task(worker.run())
    
    try:
        # Give worker time to initialize
        await asyncio.sleep(1)
        logger.info("Worker started in background")
        
        # 3. Create HTTP client
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
            timeout=180.0  # Tencent can take 60-120s
        ) as client:
            
            # 4. POST /task with Tencent provider
            logger.info("Step 1: Creating task via HTTP POST /task")
            task_payload = {
                "task_type": "text-to-image",
                "provider": "tencent",
                "params": {
                    "model": "Hunyuan",
                    "prompt": "A futuristic city with flying cars, cyberpunk style, 8k",
                    "model_name": "Hunyuan",
                    "model_version": "3.0",
                    "aspect_ratio": "16:9",
                    "resolution": "1024x576"
                },
                "priority": "normal"
            }
            
            response = await client.post("/task", json=task_payload)
            assert response.status_code == 200, f"Failed to create task: {response.text}"
            
            task_data = response.json()
            task_id = task_data["task_id"]
            logger.info(f"Task created with ID: {task_id}")
            assert task_data["status"] == "pending"
            
            # 5. Poll GET /task/{task_id} until completion
            logger.info("Step 2: Polling task status...")
            max_wait = 150  # 150 seconds timeout
            poll_interval = 3  # Poll every 3 seconds
            elapsed = 0
            
            final_status = None
            final_result = None
            
            while elapsed < max_wait:
                await asyncio.sleep(poll_interval)
                elapsed += poll_interval
                
                status_response = await client.get(f"/task/{task_id}")
                assert status_response.status_code == 200
                
                status_data = status_response.json()
                current_status = status_data["status"]
                logger.info(f"[{elapsed}s] Task status: {current_status}, progress: {status_data.get('progress', 'N/A')}")
                
                if current_status in ["completed", "failed"]:
                    final_status = current_status
                    final_result = status_data.get("result")
                    break
            
            # 6. Verify final result
            assert final_status is not None, f"Task did not complete within {max_wait}s"
            assert final_status == "completed", f"Task failed: {final_result}"
            
            logger.success(f"Task completed successfully!")
            logger.info(f"Result: {final_result}")
            
            # 7. Validate result structure
            assert final_result is not None
            assert "result_url" in final_result or "data" in final_result
            
            # If result_url exists, verify it's a valid URL
            if "result_url" in final_result:
                result_url = final_result["result_url"]
                assert result_url.startswith("http"), f"Invalid result URL: {result_url}"
                logger.success(f"Result URL: {result_url}")
            
            # Verify provider is tencent
            assert final_result.get("provider") == "tencent"
            
    finally:
        # 8. Cleanup: Stop worker
        logger.info("Stopping worker...")
        worker.stop()
        try:
            await asyncio.wait_for(worker_task, timeout=5.0)
        except asyncio.TimeoutError:
            logger.warning("Worker did not stop gracefully, cancelling...")
            worker_task.cancel()
            try:
                await worker_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Test cleanup complete")


@pytest.mark.asyncio
@pytest.mark.integration
async def test_tencent_text_to_video_http_polling_flow():
    """
    End-to-End Integration Test for Tencent Video Generation
    
    Similar to image test but for text-to-video with longer timeout.
    """
    
    # Verify environment variables
    required_env = ["TENCENTCLOUD_SECRET_ID", "TENCENTCLOUD_SECRET_KEY"]
    for env_var in required_env:
        if not os.getenv(env_var):
            pytest.skip(f"Skipping test: {env_var} not set")
    
    from genpulse.app import create_api
    from genpulse.worker import Worker
    
    app = create_api()
    worker = Worker()
    worker_task = asyncio.create_task(worker.run())
    
    try:
        await asyncio.sleep(1)
        logger.info("Worker started for video test")
        
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
            timeout=360.0  # Video can take 3-5 minutes
        ) as client:
            
            logger.info("Step 1: Creating video task via HTTP POST /task")
            task_payload = {
                "task_type": "text-to-video",
                "provider": "tencent",
                "params": {
                    "model": "Hunyuan",
                    "prompt": "A beautiful sunset over the mountains, cinematic style",
                    "model_name": "Hunyuan",
                    "model_version": "1.5",
                    "aspect_ratio": "16:9",
                    "resolution": "720P"
                },
                "priority": "normal"
            }
            
            response = await client.post("/task", json=task_payload)
            assert response.status_code == 200
            
            task_data = response.json()
            task_id = task_data["task_id"]
            logger.info(f"Video task created with ID: {task_id}")
            
            # Poll with longer timeout for video
            logger.info("Step 2: Polling video task status...")
            max_wait = 300  # 5 minutes
            poll_interval = 5
            elapsed = 0
            
            final_status = None
            final_result = None
            
            while elapsed < max_wait:
                await asyncio.sleep(poll_interval)
                elapsed += poll_interval
                
                status_response = await client.get(f"/task/{task_id}")
                assert status_response.status_code == 200
                
                status_data = status_response.json()
                current_status = status_data["status"]
                logger.info(f"[{elapsed}s] Video task status: {current_status}")
                
                if current_status in ["completed", "failed"]:
                    final_status = current_status
                    final_result = status_data.get("result")
                    break
            
            assert final_status is not None, f"Video task did not complete within {max_wait}s"
            assert final_status == "completed", f"Video task failed: {final_result}"
            
            logger.success(f"Video task completed!")
            logger.info(f"Result: {final_result}")
            
            assert final_result is not None
            if "result_url" in final_result:
                result_url = final_result["result_url"]
                assert result_url.startswith("http")
                logger.success(f"Video URL: {result_url}")
            
    finally:
        logger.info("Stopping worker...")
        worker.stop()
        try:
            await asyncio.wait_for(worker_task, timeout=5.0)
        except asyncio.TimeoutError:
            worker_task.cancel()
            try:
                await worker_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Video test cleanup complete")
