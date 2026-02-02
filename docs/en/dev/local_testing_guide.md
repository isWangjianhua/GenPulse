# Local Testing & Mock Mode

This guide explains how to develop against GenPulse without needing expensive GPUs or downloading massive model files.

## 1. Concept

GenPulse engines (like `diffusers`) support a **Mock Mode**. In this mode, the engine simulates network delays and process steps but generates a synthetic "fake" image (e.g., a solid color block) instead of running a real neural network.

This allows frontend and API developers to:
- Test the full task lifecycle (Pending -> Processing -> Completed).
- Authenticate and Upload files to storage.
- Verify WebSocket/MQ event streams.

...all on a standard laptop.

## 2. Using Mock Mode

When submitting a task to the API, simply set the `model_id` to `"mock"`.

### Example Payload

```json
POST /task
{
  "task_type": "text-to-image",
  "params": {
    "provider": "diffusers",
    "model_id": "mock",
    "prompt": "This text is ignored in mock mode"
  }
}
```

### Expected Behavior

1.  **Status Updates**: You will receive progress updates (10% -> 50% -> 90%) over roughly 1-2 seconds.
2.  **Result**: The final result will be a valid URL pointing to a generated PNG file in your local storage (`data/assets/...`).

## 3. Running the Dev Environment

To start the full stack for local testing:

```bash
# 1. Start Redis (required)
docker run -d -p 6379:6379 redis

# 2. Start GenPulse in Dev Mode
uv run genpulse dev
```

You will see the logs from both the API Server and the Worker in your terminal.

## 4. Testing RPC Mode (Microservice)

To test the synchronous-like RPC capabilities (Direct MQ interaction without HTTP):

1.  **Ensure Worker is Running**: The Celery worker must be active.
2.  **Run the Example Client**:
    ```bash
    # This script bypasses the API and talks directly to Redis
    python examples/direct_mq_client.py "Test prompt from RPC"
    ```

3.  **Result**: You should see the script push the task, wait (displaying a progress bar), and then print the final JSON result once the worker completes the job.
