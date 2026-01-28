import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock
from genpulse.infra.mq.celery_mq import CeleryMQ
from genpulse.infra.database.manager import DBManager

@pytest.fixture
def mock_redis_client():
    client = AsyncMock()
    client.ping.return_value = True
    client.lpush.return_value = 1
    # Celery might use other redis commands, mocking generally
    client.pubsub.return_value = AsyncMock()
    return client

@pytest.fixture
def mock_redis_mgr(mock_redis_client, monkeypatch):
    mgr = MagicMock(spec=CeleryMQ)
    mgr.client = mock_redis_client # Legacy attr if any
    mgr.redis_client = mock_redis_client # CeleryMQ uses this
    mgr.update_task_status = AsyncMock()
    mgr.push_task = AsyncMock()
    mgr.send_task_wait = AsyncMock()
    # pop_task is not implemented in CeleryMQ
    
    # Patch the class in all relevant modules
    # genpulse.worker is deleted, do not patch
    
    # Patch MQ factory
    monkeypatch.setattr("genpulse.infra.mq.get_mq", lambda: mgr)
    
    return mgr

@pytest.fixture
async def mock_db_manager(monkeypatch):
    mock_db = AsyncMock(spec=DBManager)
    mock_db.create_task.return_value = MagicMock(task_id="test_uuid")
    mock_db.update_task.return_value = None
    
    # Patch DBManager
    monkeypatch.setattr("genpulse.infra.database.manager.DBManager", mock_db)
    # Also patch in router if it imports class directly, but usually we patch the infra manager
    
    return mock_db
