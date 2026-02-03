import pytest
import pydantic
from pydantic import TypeAdapter
from genpulse.schemas.request import TaskRequest, TextToVideoRequest, ComfyWorkflowRequest

adapter = TypeAdapter(TaskRequest)


def test_volcengine_text_to_video_parsing():
    """Test VolcEngine text-to-video request parsing."""
    data = {
        "task_type": "text-to-video",
        "params": {
            "provider": "volcengine",
            "model": "video-1.0",
            "content": [{"type": "text", "text": "A beautiful sunset"}],
            "resolution": "720p"
        }
    }
    req = adapter.validate_python(data)
    
    assert isinstance(req, TextToVideoRequest)
    assert req.task_type == "text-to-video"
    assert req.params.provider == "volcengine"
    assert req.params.model == "video-1.0"


def test_kling_text_to_video_parsing():
    """Test Kling text-to-video request parsing."""
    data = {
        "task_type": "text-to-video",
        "params": {
            "provider": "kling",
            "model_name": "kling-v1",
            "prompt": "A dragon flying",
            "duration": "5"
        }
    }
    req = adapter.validate_python(data)
    
    assert isinstance(req, TextToVideoRequest)
    assert req.params.provider == "kling"
    assert req.params.prompt == "A dragon flying"


def test_comfy_workflow_parsing():
    """Test ComfyUI workflow request parsing."""
    data = {
        "task_type": "comfy-workflow",
        "params": {
            "provider": "comfyui",
            "workflow": {"1": {"class_type": "CheckpointLoaderSimple"}},
            "inputs": {"checkpoint": "sd_xl_base_1.0.safetensors"}
        }
    }
    req = adapter.validate_python(data)
    
    assert isinstance(req, ComfyWorkflowRequest)
    assert req.params.provider == "comfyui"
    assert req.params.inputs["checkpoint"] == "sd_xl_base_1.0.safetensors"


def test_invalid_provider_for_task_type():
    """Test that using an invalid provider for a task type fails validation."""
    # Kling is not supported for text-to-image
    data = {
        "task_type": "text-to-image",
        "params": {
            "provider": "kling",
            "model": "kling-v1",
            "prompt": "test"
        }
    }
    
    with pytest.raises(pydantic.ValidationError):
        adapter.validate_python(data)


def test_invalid_task_type():
    """Test that an invalid task_type fails validation."""
    data = {
        "task_type": "invalid-task-type",
        "params": {
            "provider": "volcengine",
            "model": "video-1.0"
        }
    }
    
    with pytest.raises(pydantic.ValidationError):
        adapter.validate_python(data)


def test_missing_required_field_in_params():
    """Test that missing required fields in params fail validation."""
    # VolcVideoParams requires 'content'
    data = {
        "task_type": "text-to-video",
        "params": {
            "provider": "volcengine",
            "model": "video-1.0"
            # Missing 'content' which is required
        }
    }
    
    with pytest.raises(pydantic.ValidationError) as excinfo:
        adapter.validate_python(data)
    
    assert "content" in str(excinfo.value)


def test_provider_field_in_params():
    """Test that provider field is correctly placed inside params."""
    data = {
        "task_type": "text-to-video",
        "params": {
            "provider": "minimax",
            "model": "video-01",
            "prompt": "A flowing river"
        }
    }
    
    req = adapter.validate_python(data)
    
    # Verify provider is accessible from params
    assert req.params.provider == "minimax"
    assert hasattr(req.params, "model")
    assert hasattr(req.params, "prompt")
