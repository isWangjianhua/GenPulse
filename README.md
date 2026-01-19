# GenPulse

> **High-Concurrency Generative AI Backend System**
>
> 🇨🇳 [中文文档](./README_CN.md)

GenPulse is a robust backend system designed to orchestrate complex Generative AI workflows (Image, Video, Audio) at scale. It provides reliable task scheduling, real-time status tracking, and unified asset management for AI applications.

---

## 🚀 Core Features

*   **Task Orchestration**: Efficiently manages long-running AI generation tasks using asynchronous queues (Redis MQ).
*   **Reliable State Tracking**: Implements a "Double-Sync" mechanism—real-time updates via Redis Pub/Sub for speed, and PostgreSQL persistence for auditability and reliability.
*   **Unified Storage Layer**: Abstracted asset management supporting Local Storage and S3/OSS.
*   **ComfyUI & Diffusers Native Support**: Choice between node-based ComfyUI workflows or high-performance native `diffusers` pipelines for image generation.
*   **Scalable Architecture**: decoupled ingestion, dispatching, and execution layers built with **FastAPI**, **SQLAlchemy (Async)**, and **Redis**.

---

## 🛠️ Usage

### Submitting a Workflow
Submit a ComfyUI workflow JSON to start a generation task.

```http
POST /task
Content-Type: application/json

{
  "task_type": "comfyui",
  "params": {
    "workflow": { ... }, // Standard ComfyUI API JSON
    "server_address": "127.0.0.1:8188"
  }
}
```

### Response
Pass back a tracking ID immediately.

```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "message": "Task queued"
}
```

### Retrieving Results
Poll or listen for updates to get the generated asset URLs.

```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "result": {
    "images": [
      "http://api.genpulse.com/assets/550e8400.../result_0.png"
    ]
  }
}
```

---

## 📦 Installation

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/your-org/genpulse.git
    cd genpulse
    ```

2.  **Start Infrastructure** (Requires Docker):
    ```bash
    docker-compose up -d
    ```

3.  **Install dependencies**:
    ```bash
    uv sync
    ```

4.  **Configure Environment**:
    Create a `.env` file:
    ```ini
    DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/genpulse
    REDIS_URL=redis://localhost:6379/0
    STORAGE_TYPE=local # or s3
    
    # If using MinIO (S3 Local):
    # STORAGE_TYPE=s3
    # S3_ENDPOINT_URL=http://localhost:9000
    # S3_ACCESS_KEY=minioadmin
    # S3_SECRET_KEY=minioadmin
    ```

5.  **Run**:
    ```bash
    # Start API
    uv run uvicorn core.gateway:app --reload
    
    # Start Worker
    uv run python -m core.worker
    ```

---

## 👨‍💻 Development

We follow a **Dev -> Test -> Main** branching strategy for stability.
Please refer to internal documentation for contribution guidelines.
