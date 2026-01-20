import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from genpulse.engines.comfy_engine import ComfyEngine

@pytest.mark.asyncio
async def test_comfy_engine_execute_success():
    # Setup
    engine = ComfyEngine()
    task = {
        "task_id": "test_task_123",
        "params": {
            "workflow": {"6": {"inputs": {"text": "a cute cat"}}},
            "server_address": "http://localhost:8188"
        }
    }
    
    mock_update_status = AsyncMock()
    context = {"update_status": mock_update_status}
    
    mock_images = [b"image_data_1", b"image_data_2"]
    
    # Mock ComfyClient
    with patch("genpulse.engines.comfy_engine.ComfyClient") as MockClient:
        mock_client_instance = MockClient.return_value
        mock_client_instance.queue_prompt = AsyncMock(return_value="prompt_123")
        mock_client_instance.wait_for_completion = AsyncMock(return_value=mock_images)
        
        # Mock storage
        with patch("genpulse.engines.comfy_engine.get_storage") as mock_get_storage:
            mock_storage_instance = AsyncMock()
            mock_get_storage.return_value = mock_storage_instance
            mock_storage_instance.upload = AsyncMock(side_effect=[
                "http://localhost:8000/assets/test_task_123/out_0.png",
                "http://localhost:8000/assets/test_task_123/out_1.png"
            ])
            
            # Execute
            result = await engine.execute(task, context)
            
            # Verify
            assert result["comfy_prompt_id"] == "prompt_123"
            assert len(result["images"]) == 2
            assert result["count"] == 2
            assert "out_0" in result["images"][0]
            
            # Verify status updates
            assert mock_update_status.call_count >= 3
            mock_client_instance.queue_prompt.assert_called_once_with(task["params"]["workflow"])
            mock_client_instance.wait_for_completion.assert_called_once_with("prompt_123")
