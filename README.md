# GenPulse

> **High-Concurrency Generative AI Backend System**
>
> 🇨🇳 [中文文档](./README_CN.md)

GenPulse is a robust backend system designed to orchestrate complex Generative AI workflows (Image, Video, Audio) at scale. It provides reliable task scheduling, real-time status tracking, and unified asset management for AI applications, supporting **7+ Major Cloud Providers**.

---

## 🚀 Core Features

*   **Multi-Model Integrity**: Unified interface for **Text-to-Image**, **Text-to-Video**, and **Image-to-Video** across multiple providers.
*   **Broad Provider Support**: Out-of-the-box support for **VolcEngine (ByteDance)**, **Tencent Cloud**, **Baidu Cloud**, **Kling AI**, **Minimax**, **DashScope (Alibaba)**, and **ComfyUI**.
*   **Task Orchestration**: Efficiently manages long-running AI generation tasks using asynchronous queues (**Redis MQ** / **RabbitMQ**).
*   **Reliable State Tracking**: Implements a "Double-Sync" mechanism—real-time updates via MQ Pub/Sub for speed, and PostgreSQL persistence for auditability.
*   **Unified Storage Layer**: Abstracted asset management supporting Local Storage and S3/OSS.
*   **Scalable Architecture**: Decoupled ingestion, dispatching, and execution layers built with **FastAPI**, **SQLAlchemy (Async)**, and **Redis**.

---

## 🧩 Supported Providers

| Provider | ID | Capabilities |
| :--- | :--- | :--- |
| **VolcEngine** | `volcengine` | Image Gen, Video Gen |
| **Tencent Cloud** | `tencent` | Image Gen (Hunyuan), Video Gen |
| **Baidu Cloud** | `baidu` | Text-to-Video, Image-to-Video |
| **Kling AI** | `kling` | High-Quality Video Generation |
| **Minimax** | `minimax` | Video Generation, Speech |
| **DashScope** | `dashscope` | Image Gen (Wanx), Video Gen |
| **ComfyUI** | `comfyui` | Custom Node Workflows |
| **Diffusers** | `diffusers` | Local Inference |

---

## 🛠️ Usage

### Submitting a Video Task
Submit a `text-to-video` task with your preferred provider.

```http
POST /task
Content-Type: application/json

{
  "task_type": "text-to-video",
  "params": {
    "provider": "kling",
    "prompt": "a cinematic drone shot of a futuristic city at sunset",
    "model_name": "kling-v1"
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
    "video_url": "https://api.genpulse.com/assets/2026/01/24/result.mp4",
    "cover_url": "https://api.genpulse.com/assets/2026/01/24/cover.jpg"
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
    Create a `.env` file from `.env.example`:
    ```ini
    DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/genpulse
    REDIS_URL=redis://localhost:6379/0
    
    # Provider Keys (Add as needed)
    VOLC_ACCESS_KEY=...
    VOLC_SECRET_KEY=...
    KLING_AK=...
    KLING_SK=...
    ```

5.  **Run**:
    ```bash
    # Start API and Worker in one go (Dev mode)
    uv run genpulse dev
    ```

---

## 👨‍💻 Development

We follow a **Dev -> Test -> Main** branching strategy for stability.
Please refer to [AGENTS.md](./AGENTS.md) for detailed contribution guidelines and coding standards.
