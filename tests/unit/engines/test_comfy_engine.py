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
    mock_instance.check_health.return_value = True
    
    # Mock listen_progress to be an async generator
    async def mock_listen_progress(prompt_id):
        yield {"type": "progress", "value": 50, "max": 100, "node": "test_node"}
        yield {"type": "completed"}
    
    mock_instance.listen_progress = mock_listen_progress
    mock_instance.get_history.return_value = {
        "prompt_123": {
            "outputs": {
                "9": {
                    "images": [
                        {"filename": "image1.png", "subfolder": "", "type": "output"},
                        {"filename": "image2.png", "subfolder": "", "type": "output"}
                    ]
                }
            }
        }
    }
    mock_instance.get_image.side_effect = lambda *args: b"fake_image_data"
    
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
    Then:  It queues prompt, listens for progress, fetches images from history, and returns URLs
    """
    engine = ComfyEngine()
    task = {
        "task_id": "task_123",
        "params": {
            "workflow": {
                "3": {
                    "inputs": {"text": "test prompt"},
                    "class_type": "CLIPTextEncode",
                    "_meta": {"title": "Positive Prompt"}
                }
            },
            "server_address": "http://test:8188"
        }
    }
    
    # Execute
    result = await engine.execute(task, task_context)
    
    # Assertions
    assert result["prompt_id"] == "prompt_123"
    assert len(result["images"]) == 2
    assert "http://mock/comfy/task_123/image1.png" in result["images"][0]
    
    # Verify Interactions
    mock_comfy_client.queue_prompt.assert_called_once()
    # Verify workflow was passed (exact match depends on apply_params logic, just check called)
    assert mock_storage.upload.call_count == 2
    
    # Verify Status Updates
    assert task_context.update_status.call_count >= 1
