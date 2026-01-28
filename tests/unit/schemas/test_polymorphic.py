import pytest
import pydantic
from genpulse.schemas.request import TaskRequest, VolcRequest, ComfyRequest

def test_volc_request_parsing():
    data = {
        "task_type": "text-to-video",
        "provider": "volcengine",
        "params": {
            "model": "doubao-vid-1.0",
            "prompt": "test",
            "width": 100,
            "height": 100
        }
    }
    # Validate using Pydantic Adapter
    from pydantic import TypeAdapter
    adapter = TypeAdapter(TaskRequest)
    req = adapter.validate_python(data)
    
    assert isinstance(req, VolcRequest)
    assert req.params.prompt == "test"

def test_comfy_request_parsing():
    data = {
        "task_type": "comfy-workflow",
        "provider": "comfyui",
        "params": {
            "workflow": {"1": {}},
            "inputs": {"a": 1}
        }
    }
    from pydantic import TypeAdapter
    adapter = TypeAdapter(TaskRequest)
    req = adapter.validate_python(data)
    
    assert isinstance(req, ComfyRequest)
    assert req.params.inputs["a"] == 1

def test_invalid_provider():
    data = {
        "task_type": "text-to-video",
        "provider": "invalid_provider",
        "params": {}
    }
    from pydantic import TypeAdapter
    adapter = TypeAdapter(TaskRequest)
    
    with pytest.raises(pydantic.ValidationError):
        adapter.validate_python(data)

def test_missing_params_field():
    # Volc params requires 'prompt'
    data = {
        "task_type": "text-to-video",
        "provider": "volcengine",
        "params": {
            "model": "doubao"
            # Missing prompt
        }
    }
    from pydantic import TypeAdapter
    adapter = TypeAdapter(TaskRequest)
    
    with pytest.raises(pydantic.ValidationError) as excinfo:
        adapter.validate_python(data)
    
    assert "prompt" in str(excinfo.value)
