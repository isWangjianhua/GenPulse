import pytest
import json
import asyncio
from unittest.mock import AsyncMock
from genpulse.processing import TaskProcessor
from genpulse.types import TaskStatus
from genpulse.handlers.base import BaseHandler
from genpulse.handlers.registry import registry

@pytest.mark.asyncio
async def test_worker_sync_db_and_redis(mock_redis_mgr, mock_db_manager):
    # Setup
    task_id = "test-sync-uuid"
    task_type = "text-to-video" # Use a standard type
    params = {"prompt": "test sync prompt", "provider": "mock"}
    
    # 1. Mock DB create behavior
    mock_db_manager.create_task.return_value = None
    
    # 2. Initialize Processor (instead of Worker)
    processor = TaskProcessor()
    
    # Important: Mock rate limiter to avoid real Redis connection
    processor.rate_limiter = AsyncMock()
    processor.rate_limiter.acquire.return_value = True
    
    # Ensure mq is the mock (conftest should handle this via get_mq patch, but being safe)
    processor.mq = mock_redis_mgr
    
    task_data = {
        "task_id": task_id,
        "task_type": task_type,
        "params": params
    }
    
    class MockHandler(BaseHandler):
        # Sync validation as per BaseHandler interface
        def validate_params(self, params): return True
        async def execute(self, task, context):
            await context.set_processing(50)
            return {"video_url": "http://mock.com/vid.mp4"}
            
    # Save original handler getter
    original_get = registry.get_handler
    # Patch registry
    registry.get_handler = lambda t: MockHandler
    
    try:
        # Run process
        await processor.process(json.dumps(task_data))
        
        # 3. Verify Redis update calls
        assert mock_redis_mgr.update_task_status.call_count >= 1
        
        # Verify final completion
        calls = mock_redis_mgr.update_task_status.call_args_list
        # Check last call
        # MockHandler calls set_processing(50) -> update_task_status(PROCESSING, 50)
        # Then processor calls update_task_status(COMPLETED, 100)
        
        # Let's check if COMPLETED was called at least once
        completed_calls = [
            c for c in calls 
            if c[0][0] == task_id and c[0][1] == TaskStatus.COMPLETED
        ]
        assert len(completed_calls) > 0, "Task was not marked as COMPLETED"

    finally:
        # Restore registry
        registry.get_handler = original_get
