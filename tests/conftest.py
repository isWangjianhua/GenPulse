import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock
from infra.mq.redis_mq import RedisMQ
from infra.database.manager import DBManager

@pytest.fixture
def mock_redis_client():
    client = AsyncMock()
    client.ping.return_value = True
    client.lpush.return_value = 1
    client.brpop.return_value = ("test_queue", '{"task_id": "test"}')
    return client

@pytest.fixture
def mock_redis_mgr(mock_redis_client, monkeypatch):
    mgr = MagicMock(spec=RedisMQ)
    mgr.client = mock_redis_client
    mgr.update_task_status = AsyncMock()
    mgr.push_task = AsyncMock()
    mgr.pop_task = AsyncMock()
    
    # Patch the class in all relevant modules
    monkeypatch.setattr("api.main.RedisManager", lambda: mgr)
    monkeypatch.setattr("worker.main.RedisManager", lambda: mgr)
    monkeypatch.setattr("infra.mq.redis_mq.RedisMQ", lambda: mgr)
    
    # Also patch instances if they already exist
    monkeypatch.setattr("api.main.mq", mgr)
    return mgr

@pytest.fixture
async def mock_db_manager(monkeypatch):
    mock_db = AsyncMock(spec=DBManager)
    mock_db.create_task.return_value = MagicMock(task_id="test_uuid")
    mock_db.update_task.return_value = None
    monkeypatch.setattr("api.main.DBManager", mock_db)
    monkeypatch.setattr("worker.main.DBManager", mock_db)
    return mock_db
