# API Reference

GenPulse provides a RESTful API with strong typing and polymorphic tasks.

## Base URL
Local: `http://localhost:8000`

---

## 1. Create Task
**POST** `/task`

Creates a new generation task. You can use either the **Generic Interface** (recommended) or **Engine Direct Interface**.

### 1.1 Generic Interface (Recommended)
Use standard task types (`text-to-image`, `text-to-video`) and switch providers using the `provider` field.

**Fields:**
| Field | Type | Description |
|-------|------|-------------|
| `task_type` | string | `text-to-image`, `text-to-video`, `image-to-video` |
| `provider` | string | `comfyui`, `volcengine`, `kling`, `baidu`, `tencent`, `minimax` |
| `params` | object | Provider-specific parameters (polymorphic) |

**Example: Text-to-Image (via ComfyUI):**
GenPulse automatically maps these params to the default ComfyUI template (`sdxl_t2i`).
```json
{
  "task_type": "text-to-image",
  "provider": "comfyui",
  "params": {
    "prompt": "A cyberpunk city with neon lights",
    "negative_prompt": "blurry, low quality",
    "width": 1024,
    "height": 1024,
    "model": "sdxl" // Optional: maps to template name
  }
}
```

**Example: Text-to-Video (via Kling AI):**
```json
{
  "task_type": "text-to-video",
  "provider": "kling",
  "params": {
    "model": "kling-v1",
    "prompt": "A futuristic drone flying through a canyon",
    "duration": 5,
    "aspect_ratio": "16:9"
  }
}
```

### 1.2 Engine Direct Interface (Advanced)
Directly invoke a specific execution engine. Useful for accessing advanced features or custom workflows.

**Provider: ComfyUI Engine**
Execute specific templates or raw workflows.

**Mode A: Template (Recommended)**
Use pre-defined JSON templates on the server (`src/genpulse/templates/comfy/`).
```json
{
  "task_type": "comfyui", 
  "params": {
    "template_name": "sdxl_t2i",
    "inputs": {
       "seed": 42,
       "prompt": "Forest landscape",
       "width_height": 1024 // If template uses custom logic
    }
  }
}
```

**Mode B: Raw Workflow**
Pass the full ComfyUI API JSON format.
(Nodes must have titles named `INPUT_varname` for variable injection)
```json
{
  "task_type": "comfyui",
  "params": {
    "workflow": { 
      "3": { "class_type": "KSampler", ... } 
    },
    "inputs": {
       "seed": 999
    },
    "server_address": "http://custom-comfy-host:8188"
  }
}
```

---

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
Use this `url` in `image_url` or `inputs` fields of your Task.

---

## 3. Query Status
**GET** `/task/{task_id}`

Returns the real-time status and result.

**Response:**
```json
{
  "task_id": "uuid-1234",
  "status": "completed",
  "progress": 100,
  "result": {
    "images": ["https://s3.../1.png"],
    "image_url": "https://s3.../1.png"
  },
  "error": null
}
```
