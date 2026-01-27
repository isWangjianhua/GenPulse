"""
Unit tests for ComfyEngine using pytest and pytest-mock.
"""
import pytest
from unittest.mock import AsyncMock
from genpulse.engines.comfy_engine import ComfyEngine
from genpulse.types import TaskContext

@pytest.fixture
def mock_storage(mocker):
    """Fixture for mocked storage."""
    mock = AsyncMock()
    mock.upload = AsyncMock(side_effect=lambda path, f, content_type: f"http://mock/{path}")
    mocker.patch("genpulse.engines.comfy_engine.get_storage", return_value=mock)
    return mock

@pytest.fixture
def mock_comfy_client(mocker):
    """Fixture for mocked ComfyClient."""
    mock_instance = AsyncMock()
    # Setup default return values
    mock_instance.queue_prompt.return_value = "prompt_123"
    mock_instance.wait_for_completion.return_value = [b"image1", b"image2"]
    
    mock_cls = mocker.patch("genpulse.engines.comfy_engine.ComfyClient", return_value=mock_instance)
    return mock_instance

@pytest.fixture
def task_context():
    """Fixture for TaskContext."""
    return TaskContext(
        task_id="task_123", 
        update_status=AsyncMock()
    )

@pytest.mark.asyncio
async def test_comfy_engine_execute_success(mock_comfy_client, mock_storage, task_context):
    """
    Test successful execution of ComfyEngine.
    
    Given: A valid task with workflow params
    When:  Engine executes
    Then:  It queues prompt, waits for completion, uploads images, and returns URLs
    """
    engine = ComfyEngine()
    task = {
        "task_id": "task_123",
        "params": {
            "workflow": {"node": "data"},
            "server_address": "http://test:8188"
        }
    }
    
    # Execute
    result = await engine.execute(task, task_context)
    
    # Assertions
    assert result["comfy_prompt_id"] == "prompt_123"
    assert len(result["images"]) == 2
    assert "http://mock/task_123/out_0" in result["images"][0]
    
    # Verify Interactions
    mock_comfy_client.queue_prompt.assert_called_once_with({"node": "data"})
    mock_comfy_client.wait_for_completion.assert_called_once_with("prompt_123")
    assert mock_storage.upload.call_count == 2
    
    # Verify Status Updates (Processing -> Queuing -> Waiting -> Uploading)
    assert task_context.update_status.call_count >= 3
