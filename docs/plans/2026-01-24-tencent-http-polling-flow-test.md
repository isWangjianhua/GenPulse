# Plan: Tencent HTTP Request Polling Flow Integration Test

## 1. Goal
Create an end-to-end integration test that validates the complete HTTP request lifecycle using Tencent as the provider:
1. **HTTP Request** → POST to `/task` API endpoint
2. **MQ Dispatch** → Task enqueued to Redis
3. **Worker Processing** → Worker picks up task and routes to correct handler
4. **Handler Execution** → `TextToImageHandler` with `provider="tencent"`
5. **Polling** → TencentVodClient polls until completion
6. **Result Retrieval** → Final result URL returned

## 2. Context
- `tests/test_tencent_client.py` already validates the **client-level** polling flow
- We now need to test the **full system flow** from HTTP API to final result
- This test will use real Tencent API credentials (integration test, not unit test)

## 3. Proposed Changes

### tests/integration/test_tencent_http_flow.py [NEW]

Create a new integration test file that:

1. **Test Setup**:
   - Start FastAPI app with lifespan (DB init)
   - Start Worker in background asyncio task
   - Ensure Tencent credentials are available via environment

2. **Test Flow**:
   ```python
   async def test_tencent_text_to_image_http_flow():
       # 1. POST /task with provider="tencent"
       response = await client.post("/task", json={
           "task_type": "text-to-image",
           "provider": "tencent",
           "params": {
               "model": "Hunyuan",
               "prompt": "A futuristic city with flying cars"
           }
       })
       task_id = response.json()["task_id"]
       
       # 2. Poll GET /task/{task_id} until completed
       # (with timeout ~120s for Tencent image generation)
       
       # 3. Assert final status is "completed"
       # 4. Assert result contains valid URL
   ```

3. **Test Teardown**:
   - Stop worker gracefully
   - Clean up any test artifacts

## 4. Verification Plan

### Automated Tests

**Command to run the new test:**
```bash
cd /home/mnze/projects/GenPulse/.wt/feature-tencent-http-flow
uv run pytest tests/integration/test_tencent_http_flow.py -v -s --tb=short
```

**Prerequisites:**
- Docker containers running (Redis, PostgreSQL): `docker-compose up -d`
- Environment variables set:
  - `TENCENTCLOUD_SECRET_ID`
  - `TENCENTCLOUD_SECRET_KEY`
  - `TENCENTCLOUD_SUBAPP_ID` (optional)

**Expected Output:**
- Test creates a task via HTTP POST
- Worker processes the task using TencentClient
- Task status transitions: `pending` → `processing` → `completed`
- Final result contains a valid Tencent VOD URL

### Manual Verification (Optional)
Run the server and worker separately to observe logs:
```bash
# Terminal 1: Start API
uv run uvicorn genpulse.app:create_api --reload

# Terminal 2: Start Worker
uv run python -m genpulse worker

# Terminal 3: Send request
curl -X POST http://localhost:8000/task \
  -H "Content-Type: application/json" \
  -d '{"task_type":"text-to-image","provider":"tencent","params":{"model":"Hunyuan","prompt":"test"}}'
```

## 5. Environment Requirements
- `TENCENTCLOUD_SECRET_ID`
- `TENCENTCLOUD_SECRET_KEY`
- `TENCENTCLOUD_SUBAPP_ID` (Optional)
- Running Redis and PostgreSQL (via docker-compose)
