# ComfyUI Handler Usage Guide

## Overview
The ComfyUI Handler is a specialized execution agent that orchestrates image generation through ComfyUI and manages asset storage.

## Task Submission

### API Endpoint
```http
POST /task
Content-Type: application/json

{
  "task_type": "comfyui",
  "params": {
    "workflow": { ... },
    "server_address": "127.0.0.1:8188"
  },
  "priority": "normal"
}
```

### Parameters

- **workflow** (required): ComfyUI API format workflow JSON
  - This is the node graph exported from ComfyUI in API format
  - Example: `{"6": {"inputs": {"text": "a cute cat"}}, ...}`

- **server_address** (optional): ComfyUI server address
  - Default: `127.0.0.1:8188`
  - Format: `host:port`

## Response Format

### Success Response
```json
{
  "comfy_prompt_id": "uuid-from-comfyui",
  "images": [
    "http://localhost:8000/assets/{task_id}/out_0_abc123.png",
    "http://localhost:8000/assets/{task_id}/out_1_def456.png"
  ],
  "count": 2
}
```

## Storage Configuration

### Local Storage (Default)
Files are saved to `data/assets/` and served via `/assets/` endpoint.

### S3 Storage
Set environment variables:
```bash
STORAGE_TYPE=s3
S3_ENDPOINT_URL=https://s3.amazonaws.com
S3_ACCESS_KEY=your_access_key
S3_SECRET_KEY=your_secret_key
S3_BUCKET_NAME=genpulse
S3_REGION_NAME=us-east-1
```

For Aliyun OSS:
```bash
S3_ENDPOINT_URL=https://oss-cn-hangzhou.aliyuncs.com
S3_ACCESS_KEY=your_aliyun_key
S3_SECRET_KEY=your_aliyun_secret
S3_BUCKET_NAME=your_bucket
```

## Example Workflow

1. **Submit Task**:
```bash
curl -X POST http://localhost:8000/task \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "comfyui",
    "params": {
      "workflow": {"6": {"inputs": {"text": "a beautiful landscape"}}},
      "server_address": "127.0.0.1:8188"
    }
  }'
```

2. **Check Status**:
```bash
curl http://localhost:8000/task/{task_id}
```

3. **Access Result**:
The response will contain URLs to generated images that can be accessed directly.

## Notes

- ComfyUI must be running and accessible at the specified address
- The handler waits for completion via WebSocket connection
- All generated images are automatically uploaded to configured storage
- Task progress is synchronized to both Redis and PostgreSQL
