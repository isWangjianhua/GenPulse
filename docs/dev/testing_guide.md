# Testing Guide

GenPulse uses `pytest` for testing. We follow a TDD approach and prioritize integration tests to ensure that all system components (Gateway, Worker, DB, Redis) work together correctly.

## 1. Running Tests

To run all tests:
```bash
uv run pytest
```

To run a specific test file:
```bash
uv run pytest tests/integration/test_gateway_workflow.py
```

## 2. Test Structure

- `tests/core/`: Unit tests for core system logic.
- `tests/integration/`: Integration tests that verify the flow between multiple components.
- `tests/conftest.py`: Defines shared fixtures and mocks.

## 3. Mocks vs. Real Services

By default, our integration tests use **Mocks** for external services (Redis and PostgreSQL) to ensure they can run in any environment (including CI/CD pipelines) without requiring a full infrastructure setup.

Shared fixtures in `tests/conftest.py`:
- `mock_redis_mgr`: A mocked version of the `RedisManager`.
- `mock_db_manager`: A mocked version of the `DBManager`.

Example usage:
```python
@pytest.mark.asyncio
async def test_my_feature(mock_redis_mgr, mock_db_manager):
    # Your test logic here
    pass
```

## 4. Testing Handlers

When testing a new handler, you should simulate the worker picking up the task.

Example:
```python
@pytest.mark.asyncio
async def test_my_handler(mock_redis_mgr, mock_db_manager):
    worker = Worker()
    worker._discover_handlers() # Ensure handlers are registered
    
    task_json = json.dumps({
        "task_id": "test-uuid",
        "task_type": "my-handler-type",
        "params": {...}
    })
    
    await worker.process_task(task_json)
    
    # Verify DB/Redis updates
    mock_db_manager.update_task.assert_called()
```

## 5. Local Infrastructure Testing

If you want to run tests against real local services, ensure you have the infrastructure running:
```bash
docker-compose up -d
```
Then you can write tests that do not use the `mock_*` fixtures. Note that these tests might be slower and require cleanup.

## 6. ComfyUI Testing

For ComfyUI-related tests, we usually mock the `ComfyClient` to avoid needing a real ComfyUI instance running.

```python
with patch("handlers.comfy_handler.ComfyClient", return_value=mock_client_instance):
    # run test
```
