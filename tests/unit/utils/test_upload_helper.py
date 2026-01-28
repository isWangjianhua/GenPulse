import pytest
import base64
from genpulse.utils.upload_helper import process_base64_inputs
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_base64_upload_simple(monkeypatch):
    mock_storage = AsyncMock()
    mock_storage.upload.return_value = "http://s3/test.png"
    
    monkeypatch.setattr("genpulse.utils.upload_helper.get_storage", lambda: mock_storage)
    
    # Create valid base64
    b64_content = base64.b64encode(b"test").decode()
    data_uri = f"data:image/png;base64,{b64_content}"
    
    input_data = {
        "image": data_uri,
        "other": "normal"
    }
    
    res = await process_base64_inputs(input_data)
    assert res["image"] == "http://s3/test.png"
    assert res["other"] == "normal"
    assert mock_storage.upload.call_count == 1

@pytest.mark.asyncio
async def test_base64_upload_nested(monkeypatch):
    mock_storage = AsyncMock()
    mock_storage.upload.return_value = "http://s3/nested.png"
    
    monkeypatch.setattr("genpulse.utils.upload_helper.get_storage", lambda: mock_storage)
    
    b64_content = base64.b64encode(b"test").decode()
    data_uri = f"data:image/png;base64,{b64_content}"
    
    input_data = {
        "wrapper": {
            "inner": data_uri
        }
    }
    
    res = await process_base64_inputs(input_data)
    assert res["wrapper"]["inner"] == "http://s3/nested.png"
