import pytest
from httpx import AsyncClient
import httpx
import json

@pytest.mark.asyncio
async def test_create_task_flow(mock_redis_mgr, mock_db_manager):
    from core.gateway import app
    """
    Verify /task endpoint:
    1. Returns 200
    2. Calls DBManager.create_task
    3. Calls RedisManager.push_task
    """
    async with AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as ac:
        payload = {
            "task_type": "txt2img",
            "params": {"prompt": "a futuristic city"},
            "priority": "high"
        }
        response = await ac.post("/task", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert "task_id" in data
    assert data["status"] == "pending"

    # Verify DB call
    mock_db_manager.create_task.assert_called_once()
    
    # Verify Redis call
    args, _ = mock_redis_mgr.push_task.call_args
    pushed_data = json.loads(args[0])
    assert pushed_data["task_type"] == "txt2img"
    assert pushed_data["params"]["prompt"] == "a futuristic city"
