import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock
from core.mq import RedisManager
from core.db_manager import DBManager

@pytest.fixture
def mock_redis_client():
    client = AsyncMock()
    client.ping.return_value = True
    client.lpush.return_value = 1
    client.brpop.return_value = ("test_queue", '{"task_id": "test"}')
    return client

@pytest.fixture
def mock_redis_mgr(mock_redis_client, monkeypatch):
    mgr = MagicMock(spec=RedisManager)
    mgr.client = mock_redis_client
    mgr.update_task_status = AsyncMock()
    mgr.push_task = AsyncMock()
    mgr.pop_task = AsyncMock()
    
    # Patch the class in all relevant modules
    monkeypatch.setattr("core.gateway.RedisManager", lambda: mgr)
    monkeypatch.setattr("core.worker.RedisManager", lambda: mgr)
    monkeypatch.setattr("core.mq.RedisManager", lambda: mgr)
    
    # Also patch instances if they already exist
    monkeypatch.setattr("core.gateway.redis_mgr", mgr)
    return mgr

@pytest.fixture
async def mock_db_manager(monkeypatch):
    mock_db = AsyncMock(spec=DBManager)
    mock_db.create_task.return_value = MagicMock(task_id="test_uuid")
    mock_db.update_task.return_value = None
    monkeypatch.setattr("core.gateway.DBManager", mock_db)
    monkeypatch.setattr("core.worker.DBManager", mock_db)
    return mock_db
