# API Reference

GenPulse provides a RESTful API with strong typing and polymorphism.

## Base URL
Local: `http://localhost:8000`

## 1. Create Task
**POST** `/task`

Creates a new generation task. The request body schema changes based on the `provider` field.

### Common Fields
| Field | Type | Description |
|-------|------|-------------|
| `task_type` | string | `text-to-video`, `image-to-video`, `comfy-workflow` |
| `priority` | string | `high`, `normal`, `low` (Default: normal) |
| `callback_url` | string | Optional webhook URL to call on completion |

### Provider: ComfyUI
Executes a raw ComfyUI workflow. Supports WebSocket streaming and binary result capture.

**Request Body:**
```json
{
  "task_type": "comfy-workflow",
  "provider": "comfyui",
  "params": {
    "workflow": { ... },  // The JSON from "Save (API Format)"
    "inputs": {
       "seed": 42,
       "prompt": "Cyberpunk city",
       "image": "https://example.com/input.png"
    },
    "server_address": "http://192.168.1.100:8188" // Optional override
  }
}
```

**Workflow Parsing Rules:**
*   Rename a node title to `INPUT_myvar` in ComfyUI.
*   GenPulse will extract it and map `params.inputs["myvar"]` to that node's primary widget (e.g., `text` for CLIPTextEncode, `seed` for KSampler).

### Provider: VolcEngine (Doubao)
```json
{
  "task_type": "text-to-video",
  "provider": "volcengine",
  "params": {
    "model": "doubao-vid-1.0",
    "prompt": "A majestic lion",
    "width": 1280,
    "height": 720
  }
}
```

### Provider: Kling AI
```json
{
  "task_type": "text-to-video",
  "provider": "kling",
  "params": {
    "model": "kling-v1",
    "prompt": "A futuristic drone",
    "duration": 5,
    "aspect_ratio": "16:9"
  }
}
```

## 2. File Upload
**POST** `/storage/upload`

Helper endpoint to upload large files (images/videos) to the configured storage (S3/OSS/Local) before creating a task.

**Response:**
```json
{
  "url": "https://genpulse-bucket.oss-cn-hangzhou.aliyuncs.com/uploads/uuid.png?Signature=...",
  "key": "uploads/uuid.png",
  "content_type": "image/png"
}
```
Use this `url` in the `image_url` or `inputs` fields of your Task.

## 3. Query Status
**GET** `/task/{task_id}`

Returns the real-time status and result.

**Response:**
```json
{
  "task_id": "uuid",
  "status": "completed",
  "progress": 100,
  "result": {
    "image_url": "https://..."
  }
}
```
