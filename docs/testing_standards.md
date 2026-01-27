# GenPulse Testing Standards

This document outlines the testing strategy, structure, and best practices for the GenPulse project.

## 1. Directory Structure

We split tests by **scope** first, then by **module**.

```text
tests/
├── unit/                   # FAST: No external I/O (DB, Network, Redis)
│   ├── clients/            # Unit tests for provider clients
│   ├── engines/            # Logic tests for AI Engines (mocked runtime)
│   ├── handlers/           # Unit tests for logic handlers
│   └── infra/              # Core infrastructure logic
│
├── integration/            # SLOWER: Uses local dependencies (Docker DB/Redis)
│   ├── api/                # Tests FastAPI endpoints with TestClient
│   ├── flows/              # Multi-component flows (e.g. Handler -> Engine)
│   └── infra/              # Real interactions with Redis/RabbitMQ
│
├── external/               # SLOW/COSTLY: Interactions with real APIs (Tencent/Volc)
│   └── ...                 # Requires API Keys.
│
├── conftest.py             # Global fixtures (event_loop, mock_redis)
└── pytest.ini              # Configuration
```

## 2. Testing Principles

### 2.1 The Testing Pyramid
- **Unit (70%)**: Business logic, parameter validation, error handling. Must run in <1s.
- **Integration (20%)**: DB queries, MQ round-trips, Helper workflows.
- **E2E/External (10%)**: Critical user paths, Smoke tests.

### 2.2 Asyncio Best Practices
Since GenPulse is heavily async:
- Use `@pytest.mark.asyncio`.
- **Fixtures Policy**: Async fixtures should generally be `function` scoped to avoid "Event loop is closed" errors.
  ```python
  @pytest.fixture
  async def async_client():
      async with AsyncClient(...) as client:
          yield client
  ```
- **Timeouts**: Use `asyncio.wait_for` in tests to prevent hanging forever on broken awaitables.

## 3. Mocking Strategy for AI

Testing AI systems is unique because model inference is slow and heavy.

### 3.1 Heavy Models
**NEVER** load real weights (e.g., SDXL, LLMs) in Unit or Integration tests.
- **Mocking**: Patch the loading function.
- **Dummy Outputs**: Return small random bytes or 1x1 pixel images as generation results.

```python
# GOOD
mock_pipeline.generate.return_value = [PIL.Image.new('RGB', (1, 1))]

# BAD
real_pipeline = StableDiffusionPipeline.from_pretrained(...) # 6GB download!
```

### 3.2 External Providers
Use `respx` or `httpx_mock` to mock HTTP interactions with Tencent/VolcEngine unless writing an `external` test.

## 4. Code Style & Patterns

### 4.1 AAA Pattern
Structure tests clearly:
- **Arrange** (Given): Setup fixtures, data.
- **Act** (When): Call the method under test.
- **Assert** (Then): Verify results.

### 4.2 Fixtures over Setup
Prefer `pytest.fixture` over `unittest.TestCase.setUp`. This enables dependency injection and better reusability.

### 4.3 Snapshot Testing (Optional)
For large JSON outputs or complex dicts, consider using `syrupy`.
```python
def test_complex_output(snapshot):
    assert result == snapshot
```

## 5. Running Tests

```bash
# Run all (Unit + Integration)
uv run pytest

# Run only Unit (Fast development loop)
uv run pytest tests/unit

# Run External (Explicit opt-in)
uv run pytest tests/external

# Debug on failure
uv run pytest -vv --pdb
```
