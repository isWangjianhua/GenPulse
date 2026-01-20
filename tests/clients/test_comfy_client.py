import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock
from genpulse.clients.comfyui.client import ComfyClient

@pytest.mark.asyncio
async def test_queue_prompt():
    client = ComfyClient("http://127.0.0.1:8188")
    prompt = {"6": {"inputs": {"text": "test"}}}
    
    expected_prompt_id = "test_prompt_id"
    
    with patch("httpx.AsyncClient.post") as mock_post:
        mock_response = MagicMock()
        mock_response.json.return_value = {"prompt_id": expected_prompt_id}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        
        prompt_id = await client.queue_prompt(prompt)
        
        assert prompt_id == expected_prompt_id
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert kwargs["json"]["prompt"] == prompt
        assert "client_id" in kwargs["json"]

@pytest.mark.asyncio
async def test_wait_for_completion():
    client = ComfyClient("http://127.0.0.1:8188")
    prompt_id = "prompt_123"
    
    # Mock WebSocket messages
    messages = [
        json.dumps({"type": "status", "data": {"status": {"exec_info": {"queue_remaining": 0}}}}),
        json.dumps({"type": "executing", "data": {"node": "6", "prompt_id": prompt_id}}),
        json.dumps({"type": "executing", "data": {"node": None, "prompt_id": prompt_id}}), # Finished
    ]
    
    # Mock Websocket
    mock_ws = AsyncMock()
    mock_ws.recv.side_effect = messages
    
    # Mock get_history and get_image
    history = {
        prompt_id: {
            "outputs": {
                "9": {
                    "images": [
                        {"filename": "out1.png", "subfolder": "", "type": "output"}
                    ]
                }
            }
        }
    }
    
    with patch("websockets.connect", return_value=MagicMock(__aenter__=AsyncMock(return_value=mock_ws))):
        with patch.object(client, "get_history", AsyncMock(return_value=history)):
            with patch.object(client, "get_image", AsyncMock(return_value=b"fake_image_bytes")):
                images = await client.wait_for_completion(prompt_id)
                
                assert len(images) == 1
                assert images[0] == b"fake_image_bytes"
                client.get_image.assert_called_once_with("out1.png", "", "output")
