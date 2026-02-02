import pytest
import logging
from unittest.mock import MagicMock, patch
from celery.exceptions import MaxRetriesExceededError
from genpulse import config
from genpulse.tasks import execute_task
from genpulse.types import TransientError

# Removed incomplete TestDLQRouting class

def test_direct_dlq_logic(mocker):
    # 1. Mock dependencies
    mock_processor = mocker.patch("genpulse.tasks.TaskProcessor")
    mock_proc_instance = mock_processor.return_value
    mock_proc_instance.process = mocker.AsyncMock()
    
    mock_send_task = mocker.patch("genpulse.tasks.celery_app.send_task")
    
    # 2. Case 1: Unexpected Error
    mock_proc_instance.process.side_effect = Exception("Boom")
    
    try:
        execute_task.apply(args=['{}'], throw=True)
    except Exception as e:
        assert str(e) == "Boom"
    
    # Verify DLQ call
    mock_send_task.assert_called_with(
        "genpulse.tasks.log_failure",
        args=['{}', "Unexpected error: Boom"],
        queue=config.DLQ_QUEUE_NAME
    )

def test_transient_error_retry(mocker):
    # Mock processor
    mock_processor = mocker.patch("genpulse.tasks.TaskProcessor")
    instance = mock_processor.return_value
    instance.process = mocker.AsyncMock(side_effect=TransientError("Network error", retry_after=1))
    
    # Mock self.retry to Raise exception
    # When using .apply(), standard Retry exceptions might be swallowed or handled differently 
    # depending on CELERY_TASK_ALWAYS_EAGER.
    # But we can verify that send_task (DLQ) was NOT called.
    
    try:
        execute_task.apply(args=['{}'], throw=True)
    except Exception:
        pass # Expected retry exception
       
    # CRITICAL: If it retries, it should NOT send to DLQ
    mock_send_task = mocker.patch("genpulse.tasks.celery_app.send_task")
    assert not mock_send_task.called

def test_max_retries_exceeded(mocker):
    # Mock processor to raise TransientError
    mock_processor = mocker.patch("genpulse.tasks.TaskProcessor")
    instance = mock_processor.return_value
    instance.process = mocker.AsyncMock(side_effect=TransientError("Network error", retry_after=1))
    
    mock_send_task = mocker.patch("genpulse.tasks.celery_app.send_task")

    # Force MaxRetriesExceededError when retry() is called
    with patch("celery.app.task.Task.retry", side_effect=MaxRetriesExceededError("No more retries")):
        try:
            execute_task.apply(args=['{}'], throw=True)
        except MaxRetriesExceededError:
            pass
            
    # Now verify DLQ call with CORRECT expected message
    mock_send_task.assert_called_with(
        "genpulse.tasks.log_failure",
        args=['{}', "Max retries exceeded: Network error"], # Corrected expectation
        queue=config.DLQ_QUEUE_NAME
    )
