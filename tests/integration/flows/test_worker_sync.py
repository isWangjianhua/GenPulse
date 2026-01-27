import pytest
import json
import asyncio
from core.worker import Worker
from core.db_manager import DBManager
from core.mq import RedisManager
from core.models import Task
from sqlalchemy import select

@pytest.mark.asyncio
async def test_worker_sync_db_and_redis(mock_redis_mgr, mock_db_manager):
    # Setup
    task_id = "test-sync-uuid"
    task_type = "z-image"
    params = {"prompt": "test sync prompt"}
    
    # 1. Mock DB create behavior
    mock_db_manager.create_task.return_value = None
    
    worker = Worker()
    worker._discover_handlers()
    
    task_data = {
        "task_id": task_id,
        "task_type": task_type,
        "params": params
    }
    
    # Run process_task
    await worker.process_task(json.dumps(task_data))
    
    # 3. Verify DB update calls
    # Should be called multiple times: processing, then final completed
    assert mock_db_manager.update_task.call_count >= 2
    
    # Verify final completion call
    last_db_call = mock_db_manager.update_task.call_args_list[-1]
    assert last_db_call.args[0] == task_id
    assert last_db_call.args[1] == "completed"
    assert last_db_call.kwargs["progress"] == 100
    
    # 4. Verify Redis update calls
    assert mock_redis_mgr.update_task_status.call_count >= 2
    last_redis_call = mock_redis_mgr.update_task_status.call_args_list[-1]
    assert last_redis_call.args[0] == task_id
    assert last_redis_call.args[1] == "completed"
    assert last_redis_call.kwargs["progress"] == 100
