import pytest
import io
import os
import json
from unittest.mock import AsyncMock, patch, MagicMock
from genpulse.worker import Worker
from genpulse.infra.storage import get_storage
from genpulse import config

@pytest.mark.asyncio
async def test_end_to_end_local_comfy_flow():
    """
    Test the flow from Worker popping a task to ComfyEngine execution and storage upload.
    Mocks the actual ComfyUI network calls.
    """
    worker = Worker()
    
    # Mock data
    task_id = "task_e2e_123"
    task_data = {
        "task_id": task_id,
        "task_type": "text-to-image",
        "params": {
            "provider": "comfyui",
            "workflow": {"test": "workflow"},
        }
    }
    
    # Mock update_status helper
    async def mock_update_status(status, progress=None, result=None):
        pass

    # Mock complications: 
    # 1. ComfyClient network calls
    # 2. Storage upload
    
    with patch("genpulse.engines.comfy_engine.ComfyClient") as MockClient:
        mock_client = MockClient.return_value
        mock_client.queue_prompt = AsyncMock(return_value="p_123")
        mock_client.wait_for_completion = AsyncMock(return_value=[b"fake_png_data"])
        
        # We also need to mock the storage to verify it saves in the right place
        # In local dev, storage is LocalStorageProvider saving to data/assets
        storage = get_storage()
        
        with patch.object(storage, "upload", AsyncMock(return_value=f"{config.STORAGE_BASE_URL}/{task_id}/out_0.png")) as mock_upload:
            # We bypass the MQ for this test and call the handler directly
            # Or use worker.process_task
            
            # For process_task to work, we need to mock the db update inside it
            # But we can just call the engine directly or the handler
            from genpulse.features.image.handlers import TextToImageHandler
            handler = TextToImageHandler()
            
            context = {"update_status": mock_update_status}
            result = await handler.execute(task_data, context)
            
            # Verifications
            assert result["comfy_prompt_id"] == "p_123"
            assert len(result["images"]) == 1
            assert result["images"][0].endswith(f"{task_id}/out_0.png")
            
            # Verify upload was called
            mock_upload.assert_called_once()
            args, _ = mock_upload.call_args
            assert args[0].startswith(f"{task_id}/out_0")
            assert args[1].read() == b"fake_png_data"

@pytest.mark.asyncio
async def test_static_file_serving():
    """Verify that files in storage path are served via /assets"""
    from genpulse.app import create_api
    from httpx import ASGITransport, AsyncClient
    from pathlib import Path
    
    app = create_api()
    # Create a test file
    test_dir = Path(config.STORAGE_LOCAL_PATH) / "test_mount"
    test_dir.mkdir(parents=True, exist_ok=True)
    test_file = test_dir / "hello.txt"
    test_file.write_text("world")
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/assets/test_mount/hello.txt")
        assert response.status_code == 200
        assert response.text == "world"
