import pytest
from unittest.mock import MagicMock, patch
import json
from genpulse.tasks import log_failure
from genpulse.infra.database.models import Task

# Remove async marker
def test_dlq_updates_db(mocker):
    """
    Test that the log_failure task updates the database status to FAILED.
    """
    # 1. Setup Mock DB Session
    mock_session = mocker.AsyncMock()
    mock_session_ctx = mocker.AsyncMock()
    mock_session_ctx.__aenter__.return_value = mock_session
    mock_session_ctx.__aexit__.return_value = None
    
    # Mock the async_session in its validation module
    mocker.patch("genpulse.infra.database.engine.async_session", return_value=mock_session_ctx)
    
    # Mock update statement
    mock_update = mocker.patch("sqlalchemy.update") 
    
    # 2. Input Data
    task_id = "test-db-sync-123"
    payload = json.dumps({"task_id": task_id, "params": {}})
    error_msg = "Database sync test error"

    # 3. Execution using Sync Mode
    # Since this is a sync test, no event loop is running.
    # The code under test will create a new loop and run successfully.
    res = log_failure.apply(args=[payload, error_msg]).get()
    
    # 4. Verification
    assert res["status"] == "failed"
    assert res["error"] == error_msg
    
    # Verify DB interaction
    # The 'async_session' context manager should have been entered
    assert mock_session_ctx.__aenter__.called
    
    # Verify update called
    assert mock_update.called
    assert mock_session.commit.called
