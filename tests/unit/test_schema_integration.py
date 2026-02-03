"""
Integration test to verify schema changes work end-to-end.
Tests that params.provider is correctly accessible in the workflow.
"""
import pytest
from pydantic import TypeAdapter
from genpulse.schemas.request import TaskRequest


def test_provider_field_accessible():
    """Verify that provider field is accessible from parsed request."""
    adapter = TypeAdapter(TaskRequest)
    
    # Parse a request
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
    
    # Verify we can access provider from params
    assert req.params.provider == "volcengine"
    assert req.task_type == "text-to-video"
    
    # Simulate what task.py does
    params_dict = req.params.model_dump()
    assert params_dict["provider"] == "volcengine"
    assert "model" in params_dict
    assert "content" in params_dict
    

def test_multiple_task_types_provider_access():
    """Test provider access across different task types."""
    adapter = TypeAdapter(TaskRequest)
    
    test_cases = [
        {
            "task_type": "text-to-video",
            "params": {
                "provider": "kling",
                "model_name": "kling-v1",
                "prompt": "test"
            }
        },
        {
            "task_type": "text-to-image",
            "params": {
                "provider": "minimax",
                "model": "image-01",
                "prompt": "test image"
            }
        },
        {
            "task_type": "image-to-video",
            "params": {
                "provider": "baidu",
                "model": "svd",
                "image": "https://example.com/img.jpg"
            }
        }
    ]
    
    for case in test_cases:
        req = adapter.validate_python(case)
        assert req.params.provider == case["params"]["provider"]
        assert req.task_type == case["task_type"]


def test_params_serialization_for_db():
    """Test that params can be serialized for database storage."""
    adapter = TypeAdapter(TaskRequest)
    
    data = {
        "task_type": "text-to-video",
        "priority": "high",
        "callback_url": "https://example.com/callback",
        "params": {
            "provider": "tencent",
            "model_name": "Hunyuan",
            "model_version": "1.5",
            "prompt": "A flowing river"
        }
    }
    
    req = adapter.validate_python(data)
    
    # Simulate task.py serialization
    processed_params = req.params.model_dump()
    
    # Verify serialized data contains all necessary fields
    assert processed_params["provider"] == "tencent"
    assert processed_params["model_name"] == "Hunyuan"
    assert processed_params["prompt"] == "A flowing river"
    
    # Verify task_data construction (as in create_task)
    task_data = {
        "task_type": req.task_type,
        "provider": req.params.provider,
        "params": processed_params,
        "priority": req.priority,
        "callback_url": req.callback_url
    }
    
    assert task_data["provider"] == "tencent"
    assert task_data["task_type"] == "text-to-video"
    assert task_data["priority"] == "high"
