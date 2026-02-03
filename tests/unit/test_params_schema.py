import pytest
from pydantic import ValidationError, TypeAdapter
from genpulse.schemas.request import TaskRequest

adapter = TypeAdapter(TaskRequest)


def test_text_to_video_volcengine():
    """Test Text-to-Video with VolcEngine."""
    data = {
        "task_type": "text-to-video",
        "params": {
            "provider": "volcengine",
            "model": "video-1.0",
            "content": [{"type": "text", "text": "A cat playing piano"}],
            "resolution": "720p",
            "duration": 5,
            "generate_audio": True
        }
    }
    req = adapter.validate_python(data)
    assert req.task_type == "text-to-video"
    assert req.params.provider == "volcengine"
    assert req.params.resolution == "720p"


def test_text_to_video_kling():
    """Test Text-to-Video with Kling."""
    data = {
        "task_type": "text-to-video",
        "params": {
            "provider": "kling",
            "model_name": "kling-v1",
            "prompt": "A sunset over mountains",
            "aspect_ratio": "16:9",
            "duration": "5"
        }
    }
    req = adapter.validate_python(data)
    assert req.task_type == "text-to-video"
    assert req.params.provider == "kling"
    assert req.params.model_name == "kling-v1"


def test_image_to_video_kling():
    """Test Image-to-Video with Kling."""
    data = {
        "task_type": "image-to-video",
        "params": {
            "provider": "kling",
            "model_name": "kling-v1",
            "prompt": "Make the character walk",
            "image": "https://example.com/image.jpg"
        }
    }
    req = adapter.validate_python(data)
    assert req.task_type == "image-to-video"
    assert req.params.provider == "kling"
    assert req.params.image == "https://example.com/image.jpg"


def test_text_to_image_volcengine():
    """Test Text-to-Image with VolcEngine."""
    data = {
        "task_type": "text-to-image",
        "params": {
            "provider": "volcengine",
            "model": "image-1.0",
            "prompt": "A beautiful landscape",
            "size": "2048x2048"
        }
    }
    req = adapter.validate_python(data)
    assert req.task_type == "text-to-image"
    assert req.params.provider == "volcengine"
    assert req.params.size == "2048x2048"


def test_text_to_image_minimax():
    """Test Text-to-Image with Minimax."""
    data = {
        "task_type": "text-to-image",
        "params": {
            "provider": "minimax",
            "model": "image-01",
            "prompt": "A futuristic city",
            "aspect_ratio": "16:9",
            "n": 2
        }
    }
    req = adapter.validate_python(data)
    assert req.task_type == "text-to-image"
    assert req.params.provider == "minimax"
    assert req.params.n == 2


def test_tencent_video():
    """Test Tencent Video generation."""
    data = {
        "task_type": "text-to-video",
        "params": {
            "provider": "tencent",
            "model_name": "Hunyuan",
            "model_version": "1.5",
            "prompt": "A flowing river",
            "resolution": "1080P"
        }
    }
    req = adapter.validate_python(data)
    assert req.task_type == "text-to-video"
    assert req.params.provider == "tencent"
    assert req.params.model_name == "Hunyuan"


def test_baidu_image_to_video():
    """Test Baidu Image-to-Video."""
    data = {
        "task_type": "image-to-video",
        "params": {
            "provider": "baidu",
            "model": "stable-video-diffusion",
            "image": "https://example.com/image.jpg",
            "prompt": "Make it move",
            "duration": 5
        }
    }
    req = adapter.validate_python(data)
    assert req.task_type == "image-to-video"
    assert req.params.provider == "baidu"
    assert req.params.image == "https://example.com/image.jpg"


def test_invalid_task_type():
    """Test invalid task_type."""
    data = {
        "task_type": "unknown-task",
        "params": {}
    }
    with pytest.raises(ValidationError):
        adapter.validate_python(data)


def test_invalid_provider_for_task():
    """Test provider not available for a specific task type."""
    # Kling is not in TextToImageParams union
    data = {
        "task_type": "text-to-image",
        "params": {
            "provider": "kling",  # Kling doesn't do T2I in our schema
            "model": "kling-v1",
            "prompt": "test"
        }
    }
    with pytest.raises(ValidationError):
        adapter.validate_python(data)


def test_missing_required_field():
    """Test missing required field (prompt for VolcImageParams)."""
    data = {
        "task_type": "text-to-image",
        "params": {
            "provider": "volcengine",
            "model": "image-1.0"
            # Missing 'prompt' which is required
        }
    }
    with pytest.raises(ValidationError):
        adapter.validate_python(data)


def test_comfy_workflow():
    """Test ComfyUI workflow request."""
    data = {
        "task_type": "comfy-workflow",
        "params": {
            "provider": "comfyui",
            "workflow": {"nodes": []},
            "inputs": {"prompt": "test"}
        }
    }
    req = adapter.validate_python(data)
    assert req.task_type == "comfy-workflow"
    assert req.params.provider == "comfyui"
