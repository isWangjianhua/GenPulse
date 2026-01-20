import pytest
from unittest.mock import AsyncMock, patch
from genpulse.features.image.handlers import TextToImageHandler
from genpulse import config

@pytest.mark.asyncio
async def test_diffusers_engine_mock_flow():
    """
    Verify that TextToImageHandler correctly uses DiffusersEngine in mock mode.
    """
    from genpulse.types import TaskContext
    handler = TextToImageHandler()
    
    # Mock data
    task_id = "task_diff_123"
    task_data = {
        "task_id": task_id,
        "task_type": "text-to-image",
        "params": {
            "provider": "diffusers",
            "model_id": "mock",
            "prompt": "a beautiful landscape",
        }
    }
    
    # Mock update_status
    mock_update_status = AsyncMock()
    context = TaskContext(task_id=task_id, update_status=mock_update_status)
    
    with patch("genpulse.engines.diffusers_engine.get_storage") as mock_get_storage:
        mock_storage = mock_get_storage.return_value
        mock_storage.upload = AsyncMock(return_value="http://localhost:8000/assets/task_diff_123/mock.png")
        
        result = await handler.execute(task_data, context)
        
        # Verifications
        assert result["provider"] == "diffusers"
        assert len(result["images"]) == 1
        assert "mock" in result["images"][0]
        
        # Verify status updates (using context helper methods)
        # 10 (init), 50 (generating), 90 (finalizing)
        assert mock_update_status.call_count >= 3
