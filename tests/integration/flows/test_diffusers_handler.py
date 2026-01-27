import pytest
import json
import io
from unittest.mock import MagicMock, patch, AsyncMock
from core.worker import Worker

@pytest.mark.asyncio
async def test_diffusers_handler_execution(mock_redis_mgr, mock_db_manager, monkeypatch):
    """
    Test the DiffusersHandler by mocking the pipeline and torch.
    """
    # 1. Setup mocks for diffusers and torch
    mock_pipe = MagicMock()
    mock_output = MagicMock()
    mock_image = MagicMock()
    mock_output.images = [mock_image]
    mock_pipe.return_value = mock_output
    
    # Mock StableDiffusionPipeline.from_pretrained
    mock_from_pretrained = MagicMock(return_value=mock_pipe)
    
    # Mock Storage
    mock_storage = AsyncMock()
    mock_storage.upload.return_value = "http://localhost/diffusers.png"
    
    # Apply mocks
    with patch("handlers.diffusers_handler.StableDiffusionPipeline") as mock_sd_class, \
         patch("handlers.diffusers_handler.get_storage", return_value=mock_storage), \
         patch("torch.cuda.is_available", return_value=False):
        
        mock_sd_class.from_pretrained = mock_from_pretrained
        
        # 2. Prepare task
        task_id = "test-diffusers-uuid"
        payload = {
            "task_id": task_id,
            "task_type": "diffusers_txt2img",
            "params": {
                "prompt": "a beautiful mountain",
                "model_id": "mock/model"
            }
        }
        
        # 3. Execute via Worker
        worker = Worker()
        worker._discover_handlers()
        
        await worker.process_task(json.dumps(payload))
        
        # 4. Verify
        # Check if model was "loaded"
        mock_from_pretrained.assert_called_once()
        args, kwargs = mock_from_pretrained.call_args
        assert args[0] == "mock/model"
        
        # Check if inference was called
        mock_pipe.assert_called_once()
        _, p_kwargs = mock_pipe.call_args
        assert p_kwargs["prompt"] == "a beautiful mountain"
        
        # Check if result was uploaded
        mock_storage.upload.assert_called_once()
        
        # Check DB update
        assert mock_db_manager.update_task.call_count >= 2
        last_call = mock_db_manager.update_task.call_args_list[-1]
        assert last_call.args[1] == "completed"
        assert last_call.kwargs["result"]["images"][0] == "http://localhost/diffusers.png"
