import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from genpulse.handlers.image import TextToImageHandler
from genpulse.handlers.video import TextToVideoHandler
from genpulse.types import TaskContext


@pytest.mark.asyncio
async def test_tencent_image_handler_parameter_mapping():
    """
    Unit test: Verify that TextToImageHandler correctly maps generic params to TencentImageParams
    """
    handler = TextToImageHandler()
    
    task_data = {
        "task_id": "test-123",
        "task_type": "text-to-image",
        "provider": "tencent",
        "params": {
            "provider": "tencent",
            "model": "Hunyuan",
            "prompt": "A beautiful landscape",
            "negative_prompt": "ugly, blurry",
            "model_name": "Hunyuan",
            "model_version": "3.0",
            "aspect_ratio": "16:9",
            "resolution": "1024x576"
        }
    }
    
    # Mock the TencentVodClient
    with patch("genpulse.handlers.image.get_tencent_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.is_succeeded = True
        mock_response.result_url = "https://example.com/result.png"
        mock_response.model_dump.return_value = {"TaskId": "tencent-task-123"}
        mock_response.AigcImageTask = None
        
        mock_client.generate_image = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client
        
        # Create mock context
        mock_update_status = AsyncMock()
        context = TaskContext(task_id="test-123", update_status=mock_update_status)
        
        # Execute
        result = await handler.execute(task_data, context)
        
        # Verify
        assert result["status"] == "succeeded"
        assert result["provider"] == "tencent"
        assert result["result_url"] == "https://example.com/result.png"
        
        # Verify client was called with correct parameters
        mock_client.generate_image.assert_called_once()
        call_args = mock_client.generate_image.call_args
        
        # Check that TencentImageParams was created correctly
        tencent_params = call_args[0][0]
        assert tencent_params.ModelName == "Hunyuan"
        assert tencent_params.ModelVersion == "3.0"
        assert tencent_params.Prompt == "A beautiful landscape"
        assert tencent_params.NegativePrompt == "ugly, blurry"
        assert tencent_params.OutputConfig.AspectRatio == "16:9"
        assert tencent_params.OutputConfig.Resolution == "1024x576"
        
        # Verify wait=True was passed
        assert call_args[1]["wait"] is True


@pytest.mark.asyncio
async def test_tencent_video_handler_parameter_mapping():
    """
    Unit test: Verify that TextToVideoHandler correctly maps generic params to TencentVideoParams
    """
    handler = TextToVideoHandler()
    
    task_data = {
        "task_id": "test-video-456",
        "task_type": "text-to-video",
        "provider": "tencent",
        "params": {
            "provider": "tencent",
            "model": "Hunyuan",
            "prompt": "A cinematic sunset",
            "model_name": "Hunyuan",
            "model_version": "1.5",
            "aspect_ratio": "16:9",
            "resolution": "720P"
        }
    }
    
    # Mock the TencentVodClient
    with patch("genpulse.handlers.video.get_tencent_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.is_succeeded = True
        mock_response.result_url = "https://example.com/result.mp4"
        mock_response.model_dump.return_value = {"TaskId": "tencent-video-123"}
        mock_response.AigcVideoTask = None
        
        mock_client.generate_video = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client
        
        # Create mock context
        mock_update_status = AsyncMock()
        context = TaskContext(task_id="test-video-456", update_status=mock_update_status)
        
        # Execute
        result = await handler.execute(task_data, context)
        
        # Verify
        assert result["status"] == "succeeded"
        assert result["provider"] == "tencent"
        assert result["result_url"] == "https://example.com/result.mp4"
        
        # Verify client was called with correct parameters
        mock_client.generate_video.assert_called_once()
        call_args = mock_client.generate_video.call_args
        
        # Check that TencentVideoParams was created correctly
        tencent_params = call_args[0][0]
        assert tencent_params.ModelName == "Hunyuan"
        assert tencent_params.ModelVersion == "1.5"
        assert tencent_params.Prompt == "A cinematic sunset"
        assert tencent_params.OutputConfig.AspectRatio == "16:9"
        assert tencent_params.OutputConfig.Resolution == "720P"
        
        # Verify wait=True was passed
        assert call_args[1]["wait"] is True


@pytest.mark.asyncio
async def test_tencent_handler_error_handling():
    """
    Unit test: Verify error handling when Tencent API fails
    """
    handler = TextToImageHandler()
    
    task_data = {
        "task_id": "test-error",
        "task_type": "text-to-image",
        "provider": "tencent",
        "params": {
            "provider": "tencent",
            "prompt": "Test prompt"
        }
    }
    
    with patch("genpulse.handlers.image.get_tencent_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.is_succeeded = False
        mock_response.AigcImageTask = MagicMock()
        mock_response.AigcImageTask.Message = "API Error: Invalid parameters"
        
        mock_client.generate_image = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client
        
        mock_update_status = AsyncMock()
        context = TaskContext(task_id="test-error", update_status=mock_update_status)
        
        # Execute and expect exception
        with pytest.raises(Exception) as exc_info:
            await handler.execute(task_data, context)
        
        assert "Tencent T2I failed" in str(exc_info.value)
        assert "API Error: Invalid parameters" in str(exc_info.value)
