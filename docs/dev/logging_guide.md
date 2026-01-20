# Logging & Debugging

GenPulse uses a centralized logging system based on **Loguru**. This provides structured, colorful, and automatically rotated logs.

## 1. Log Locations

- **Console**: By default, logs are printed to `stderr` with colors.
- **File**: 
    - `logs/genpulse.log`: Contains all logs (INFO and above). Rotated every 500MB, kept for 10 days.
    - `logs/error.log`: Contains only ERROR/CRITICAL logs.

## 2. Reading Logs

Format: `Time | Level | Module:Function:Line - Message`

**Example:**
```text
2026-01-20 10:00:05.123 | INFO     | genpulse.worker:process_task:62 - Processing task task_123 (text-to-image)
2026-01-20 10:00:05.456 | ERROR    | genpulse.engines.comfy_engine:execute:56 - ComfyUI execution failed: Connection Refused
```

## 3. Debugging Strategies

### 3.1 Trace Execution via Task ID
Copy the `task_id` from the API response and `grep` it in the logs:

```bash
grep "task_123" logs/genpulse.log
```

This will show you the entire lifecycle of that request across the API and Worker.

### 3.2 Adjusting Log Level

To see debug messages (including variable values and mock details), change the level in `config/config.yaml`:

```yaml
LOGGING:
  level: "DEBUG"
```

### 3.3 Common Errors

| Error | Likely Cause | Fix |
| :--- | :--- | :--- |
| `EngineError: Handler not found` | `task_type` in JSON doesn't match `@registry.register` | Check spelling in `handlers.py` decorators. |
| `Boto3 missing` | S3 storage enabled but `boto3` not installed | Run `uv add boto3`. |
| `ConnectionRefusedError` | ComfyUI is not running | Start ComfyUI manually or check `COMFY_URL` in config. |
