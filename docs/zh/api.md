# API 参考

GenPulse 提供了一个具有强类型和多态任务支持的 RESTful API。

## 基础 URL
本地: `http://localhost:8000`

---

## 1. 创建任务 (Create Task)
**POST** `/task`

创建一个新的生成任务。您可以使用**通用接口**（推荐）或**引擎直连接口**。

### 1.1 通用接口 (推荐)
使用标准任务类型 (`text-to-image`, `text-to-video`) 并通过 `provider` 字段切换供应商。

**字段:**
| 字段 | 类型 | 描述 |
|-------|------|-------------|
| `task_type` | string | `text-to-image`, `text-to-video`, `image-to-video` |
| `provider` | string | `comfyui`, `volcengine`, `kling`, `baidu`, `tencent`, `minimax` |
| `params` | object | 特定于供应商的参数 (多态) |

**示例: 文生图 (通过 ComfyUI):**
GenPulse 会自动将这些参数映射到默认的 ComfyUI 模板 (`sdxl_t2i`)。
```json
{
  "task_type": "text-to-image",
  "provider": "comfyui",
  "params": {
    "prompt": "A cyberpunk city with neon lights",
    "negative_prompt": "blurry, low quality",
    "width": 1024,
    "height": 1024,
    "model": "sdxl" // 可选: 映射到模板名称
  }
}
```

**示例: 文生视频 (通过 Kling AI):**
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

### 1.2 引擎直连接口 (高级)
直接调用特定的执行引擎。适用于访问高级功能或自定义工作流。

**Provider: ComfyUI Engine**
执行特定的模板或原始工作流。

**模式 A: 模板 (推荐)**
使用服务器上预定义的 JSON 模板 (`src/genpulse/templates/comfy/`)。
```json
{
  "task_type": "comfyui", 
  "params": {
    "template_name": "sdxl_t2i",
    "inputs": {
       "seed": 42,
       "prompt": "Forest landscape",
       "width_height": 1024 // 如果模板使用了自定义逻辑
    }
  }
}
```

**模式 B: 原始工作流 (Raw Workflow)**
传递完整的 ComfyUI API JSON 格式。
(节点标题必须命名为 `INPUT_变量名` 以进行变量注入)
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

## 2. 文件上传
**POST** `/storage/upload`

辅助端点，用于在创建任务之前将大文件（图像/视频）上传到配置的存储（S3/OSS/Local）。

**响应:**
```json
{
  "url": "https://genpulse-bucket.oss-cn-hangzhou.aliyuncs.com/uploads/uuid.png?Signature=...",
  "key": "uploads/uuid.png",
  "content_type": "image/png"
}
```
使用此 `url` 填充 Task 中的 `image_url` 或 `inputs` 字段。

---

## 3. 查询状态
**GET** `/task/{task_id}`

返回实时状态和结果。

**响应:**
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
