import pytest
import io
import json
from unittest.mock import AsyncMock, patch, MagicMock
from httpx import AsyncClient
import httpx
from core.worker import Worker
from core.storage import get_storage

@pytest.mark.asyncio
async def test_comfy_full_workflow(mock_redis_mgr, mock_db_manager, monkeypatch):
    """
    Simulate the full loop:
    1. Gateway receives ComfyUI task
    2. Worker picks it up
    3. ComfyHandler executes (mocked client)
    4. Assets are saved and URL is returned
    """
    from core.gateway import app
    
    # --- Part 1: Gateway ---
    async with AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as ac:
        payload = {
            "task_type": "comfyui",
            "params": {
                "workflow": {"6": {"inputs": {"text": "a cute cat"}}},
                "server_address": "127.0.0.1:8188"
            }
        }
        resp = await ac.post("/task", json=payload)
        assert resp.status_code == 200
        task_id = resp.json()["task_id"]

    # --- Part 2: Worker & Handler ---
    # We need to multi-mock the ComfyClient and Storage
    mock_client_instance = AsyncMock()
    mock_client_instance.queue_prompt.return_value = "mock_prompt_id"
    # Return 1 dummy image byte-string
    mock_client_instance.wait_for_completion.return_value = [b"fake_image_data"]
    
    with patch("handlers.comfy_handler.ComfyClient", return_value=mock_client_instance):
        worker = Worker()
        task_json = json.dumps({
            "task_id": task_id,
            "task_type": "comfyui",
            "params": payload["params"]
        })
        
        await worker.process_task(task_json)
    
    # --- Part 3: Verify ---
    # Check if update_task was called with completed status and URLs
    last_call = mock_db_manager.update_task.call_args_list[-1]
    assert last_call.args[1] == "completed"
    result = last_call.kwargs["result"]
    assert "images" in result
    assert result["images"][0].startswith("http://localhost:8000/assets/")
    
    # Verify file actually exists on disk (LocalStorage)
    storage = get_storage()
    # Extract relative path from URL
    rel_path = result["images"][0].split("/assets/")[1]
    import os
    from core.config import settings
    full_path = os.path.join(settings.STORAGE_LOCAL_PATH, rel_path)
    assert os.path.exists(full_path)
    
    # Cleanup
    if os.path.exists(full_path):
        os.remove(full_path)
