"""
Tests for RabbitMQ MQ implementation.

Note: These tests require a running RabbitMQ instance.
Set RABBITMQ_URL environment variable or use default: amqp://guest:guest@localhost:5672/
"""
import pytest
import json
import os

# Set MQ_TYPE to rabbitmq for these tests
os.environ["GENPULSE_MQ__TYPE"] = "rabbitmq"

from genpulse.infra.mq import get_mq
from genpulse.infra.mq.rabbitmq_mq import RabbitMQ


@pytest.fixture
async def mq():
    """Create RabbitMQ instance for testing."""
    instance = RabbitMQ()
    yield instance
    await instance.close()


@pytest.mark.asyncio
async def test_rabbitmq_ping(mq):
    """Test RabbitMQ connection."""
    result = await mq.ping()
    assert result is True


@pytest.mark.asyncio
async def test_rabbitmq_push_pop(mq):
    """Test pushing and popping tasks."""
    task_data = {
        "task_id": "test-123",
        "task_type": "text-to-image",
        "params": {"prompt": "test"}
    }
    task_json = json.dumps(task_data)
    
    # Push task
    await mq.push_task(task_json)
    
    # Pop task
    result = await mq.pop_task(timeout=2)
    assert result is not None
    queue_name, popped_data = result
    assert popped_data == task_json


@pytest.mark.asyncio
async def test_rabbitmq_status_update(mq):
    """Test task status update and retrieval."""
    task_id = "test-status-456"
    
    # Update status
    await mq.update_task_status(
        task_id,
        "processing",
        progress=50,
        result={"info": "halfway"}
    )
    
    # Get status
    status = await mq.get_task_status(task_id)
    assert status is not None
    assert status["status"] == "processing"
    assert status["progress"] == 50
    assert status["result"]["info"] == "halfway"


@pytest.mark.asyncio
async def test_rabbitmq_factory():
    """Test that get_mq() returns RabbitMQ instance when configured."""
    mq = get_mq()
    assert isinstance(mq, RabbitMQ)
    await mq.close()
