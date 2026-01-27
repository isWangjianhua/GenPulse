"""
Tests for Celery MQ implementation.

Note: These tests mock Celery to avoid requiring a running Celery worker.
"""
import pytest
import json
import os
from unittest.mock import Mock, patch, MagicMock

# Set MQ_TYPE to celery for these tests
os.environ["GENPULSE_MQ__TYPE"] = "celery"

from genpulse.infra.mq.celery_mq import CeleryMQ


@pytest.fixture
async def mq():
    """Create CeleryMQ instance for testing."""
    instance = CeleryMQ()
    yield instance
    await instance.close()


@pytest.mark.asyncio
async def test_celery_push_task(mq):
    """Test pushing tasks to Celery."""
    task_data = {
        "task_id": "test-celery-123",
        "task_type": "text-to-video",
        "params": {"prompt": "test video"}
    }
    task_json = json.dumps(task_data)
    
    # Mock celery_app.send_task
    with patch("genpulse.infra.mq.celery_mq.celery_app.send_task") as mock_send:
        await mq.push_task(task_json)
        
        # Verify send_task was called with correct arguments
        mock_send.assert_called_once_with(
            "genpulse.tasks.execute_task",
            args=[task_json],
            queue="genpulse_tasks"
        )


@pytest.mark.asyncio
async def test_celery_pop_task_raises(mq):
    """Test that pop_task raises NotImplementedError for Celery."""
    with pytest.raises(NotImplementedError):
        await mq.pop_task()


@pytest.mark.asyncio
async def test_celery_status_update(mq):
    """Test task status update and retrieval."""
    task_id = "test-celery-status-789"
    
    # Update status
    await mq.update_task_status(
        task_id,
        "completed",
        progress=100,
        result={"video_url": "https://example.com/video.mp4"}
    )
    
    # Get status
    status = await mq.get_task_status(task_id)
    assert status is not None
    assert status["status"] == "completed"
    assert status["progress"] == 100
    assert status["result"]["video_url"] == "https://example.com/video.mp4"
