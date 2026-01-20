import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock
from genpulse.infra.mq.redis_mq import RedisMQ
from genpulse.infra.database.manager import DBManager

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
    monkeypatch.setattr("genpulse.features.task.router.get_mq", lambda: mgr)
    monkeypatch.setattr("genpulse.worker.get_mq", lambda: mgr)
    monkeypatch.setattr("genpulse.infra.mq.get_mq", lambda: mgr)
    
    return mgr

@pytest.fixture
async def mock_db_manager(monkeypatch):
    mock_db = AsyncMock(spec=DBManager)
    mock_db.create_task.return_value = MagicMock(task_id="test_uuid")
    mock_db.update_task.return_value = None
    
    # Patch DBManager in routers and workers
    monkeypatch.setattr("genpulse.features.task.router.DBManager", mock_db)
    monkeypatch.setattr("genpulse.worker.DBManager", mock_db)
    monkeypatch.setattr("genpulse.infra.database.manager.DBManager", mock_db)
    
    return mock_db
