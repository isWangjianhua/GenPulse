"""
Unit tests for DiffusersEngine logic (via Handler integration).
"""
import pytest
from unittest.mock import AsyncMock
from genpulse.handlers.image import TextToImageHandler
from genpulse.types import TaskContext

@pytest.fixture
def mock_storage(mocker):
    """Fixture for mocked storage."""
    mock = AsyncMock()
    # Return a dummy URL
    mock.upload.return_value = "http://mock/asset.png"
    mocker.patch("genpulse.engines.diffusers_engine.get_storage", return_value=mock)
    return mock

@pytest.fixture
def task_context():
    return TaskContext(
        task_id="task_diff_123",
        update_status=AsyncMock()
    )

@pytest.mark.asyncio
async def test_diffusers_engine_mock_flow(mock_storage, task_context):
    """
    Verify that TextToImageHandler correctly routes to DiffusersEngine (Mock Mode).
    
    Given: A task with provider='diffusers'
    When:  Handler executes
    Then:  It generates a mock image and uploads it
    """
    handler = TextToImageHandler()
    
    task_data = {
        "task_id": "task_diff_123",
        "task_type": "text-to-image",
        "params": {
            "provider": "diffusers",
            "model_id": "mock",
            "prompt": "test prompt",
        }
    }
    
    # Execute
    result = await handler.execute(task_data, task_context)
    
    # Assertions
    assert result["provider"] == "diffusers"
    assert len(result["images"]) == 1
    assert "mock" in str(result["images"][0])
    
    # Verify interactions
    # In mock mode, it typically generates 1 image and uploads it
    mock_storage.upload.assert_called_once()
    
    # Verify status updates
    assert task_context.update_status.call_count >= 1
