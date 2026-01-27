import pytest
import asyncio
import json
from unittest.mock import MagicMock, patch, AsyncMock
from core.worker import Worker
from core.config import settings

@pytest.mark.asyncio
async def test_worker_with_local_comfy_startup(mock_redis_mgr, mock_db_manager, monkeypatch):
    """
    Verify that Worker correctly starts and stops the local ComfyUI process
    when manage_comfy=True.
    """
    mock_pm = MagicMock()
    
    with patch("core.process_manager.ComfyProcessManager", return_value=mock_pm):
        # We need to mock settings to enable local comfy for this test
        # Actually Worker(manage_comfy=True) overrides settings.COMFY_ENABLE_LOCAL logic in my implementation
        
        worker = Worker(manage_comfy=True)
        
        # We'll mock the internal loop to exit immediately
        worker.should_run = False 
        
        await worker.run()
        
        # Verify start was called
        mock_pm.start.assert_called_once()
        # Verify stop was called in finally block
        mock_pm.stop.assert_called_once()

@pytest.mark.asyncio
async def test_worker_process_task_comfyui(mock_redis_mgr, mock_db_manager, monkeypatch):
    """
    Verify that a 'comfyui' task is handled by ComfyUIHandler
    and uses the ComfyClient.
    """
    worker = Worker()
    worker._discover_handlers()
    
    task_id = "test-comfy-id"
    payload = {
        "task_id": task_id,
        "task_type": "comfyui",
        "params": {
            "workflow": {"mock": "node"},
            "server_address": "127.0.0.1:8188"
        }
    }
    
    # Mock ComfyClient to avoid real network calls
    mock_client = AsyncMock()
    mock_client.queue_prompt.return_value = "prompt-123"
    mock_client.wait_for_completion.return_value = [b"img-data"]
    
    # Mock Storage
    mock_storage = AsyncMock()
    mock_storage.upload.return_value = "http://localhost/mock.png"
    
    with patch("handlers.comfy_handler.ComfyClient", return_value=mock_client), \
         patch("handlers.comfy_handler.get_storage", return_value=mock_storage):
        
        await worker.process_task(json.dumps(payload))
        
        # Verify interactions
        mock_client.queue_prompt.assert_called_once_with({"mock": "node"})
        mock_client.wait_for_completion.assert_called_once_with("prompt-123")
        mock_storage.upload.assert_called()
        
        # Verify DB update
        assert mock_db_manager.update_task.call_count >= 2
        last_call = mock_db_manager.update_task.call_args_list[-1]
        assert last_call.args[1] == "completed"
        assert "images" in last_call.kwargs["result"]
