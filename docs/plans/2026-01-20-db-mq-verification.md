# Database & MQ Integration Verification Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task.

**Goal:** Create a robust integration test suite to verify the data flow between FastAPI Gateway, PostgreSQL (via DBManager), and Redis (via RedisManager), ensuring status synchronization works correctly.

**Architecture:**
- **Pytest** for testing.
- **unittest.mock / pytest-mock** to mock Redis and DB if needed, but prioritize real connection tests for local dev.
- **Test-Driven Development (TDD)** approach for the verification logic.

---

### Task 1: Test Environment Setup

**Files:**
- Create: `tests/conftest.py`
- Modify: `pyproject.toml` (Add test dependencies if missing)

**Step 1: Install test dependencies**
```bash
pip install pytest pytest-asyncio pytest-mock httpx
```

**Step 2: Create conftest.py**
Define mocks for Redis and DB sessions to allow running tests without external services if they are not available.

---

### Task 2: Gateway Integration Test

**Files:**
- Create: `tests/integration/test_gateway_workflow.py`

**Step 1: Write failing test for /task endpoint**
Verify that calling `/task` returns 200, creates a record in DB, and pushes to Redis.

**Step 2: Implement minimal fixes in Gateway**
(If any bugs are found during testing).

**Step 3: Run and Pass**
```bash
pytest tests/integration/test_gateway_workflow.py
```

---

### Task 3: Worker DB Sync Test

**Files:**
- Create: `tests/integration/test_worker_sync.py`

**Step 1: Write test for Worker.process_task**
Manually trigger `process_task` and verify that `DBManager.update_task` is called with the expected status and progress.

**Step 2: Verify Redis Pub/Sub trigger**
Ensure that updating task status in the worker also results in a Redis publication.

---

### Task 4: Documentation & Quality Review

**Files:**
- Create: `docs/dev/testing_guide.md`

**Step 1: Write testing guide**
Document how to run tests, how to use mocks, and the expectations for CI.

**Step 2: Use requesting-code-review skill**
Review the entire feature branch before proposing merge to `dev`.
