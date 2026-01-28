# GenPulse: High-Performance AI Orchestration Engine

**GenPulse** is a production-grade backend for orchestrating Generative AI tasks. It bridges the gap between raw AI APIs (VolcEngine, Kling, Minimax) plus local execution engines (ComfyUI) and your business applications, providing a unified, reliable, and scalable interface.

## 🚀 Key Features

*   **Multi-Provider Support**: Seamlessly switch between **VolcEngine (Doubao)**, **Kling AI**, **Minimax (Hailuo)**, and more via a single polymorphic API.
*   **Deep ComfyUI Integration**: 
    *   Execute raw ComfyUI workflows via API without UI interactions.
    *   **Auto-Parsing**: Automatically detects dynamic inputs (nodes named `INPUT_`).
    *   **Streaming**: Real-time progress updates via WebSocket.
    *   **Binary Capture**: Supports `SaveImageWebsocket` for faster, diskv-free image retrieval.
*   **Unified Storage Layer**:
    *   Automatically uploads generated assets to **AWS S3**, **Aliyun OSS**, or **MinIO**.
    *   Generates secure **Presigned URLs** for private buckets.
    *   Built-in `POST /storage/upload` API for handling large inputs (Image-to-Video).
    *   Automatic Base64 decoding and uploading for inline inputs.
*   **Robust Architecture**: 
    *   Built on **FastAPI + Celery + Redis + PostgreSQL**.
    *   Distributed Rate Limiting & Flow Control.
    *   Exponential Backoff Retries & Dead Letter Queues (DLQ) for reliability.
*   **DevOps Ready**:
    *   **Docker Compose** one-click deployment.
    *   **Admin Dashboard** (SQLAdmin) for task management.
    *   **Flower** integration for real-time worker monitoring.

## 🛠 Quick Start

### 1. Using Docker (Recommended)

```bash
# 1. Clone
git clone https://github.com/isWangjianhua/GenPulse.git
cd GenPulse

# 2. Configure (Optional)
# Edit docker-compose.yml to set S3 credentials or ComfyUI URL
# export GENPULSE_PROVIDERS__COMFY_URL="http://your-comfyui-host:8188"

# 3. Launch Stack
docker-compose up -d

# 4. Access Services
# - API Documentation: http://localhost:8000/docs
# - Admin Dashboard:   http://localhost:8000/admin
# - Flower Monitor:    http://localhost:5555
```

### 2. Local Development

```bash
# Install dependencies
uv sync

# Configure Environment
export GENPULSE_ENV=dev
export GENPULSE_REDIS__URL=redis://localhost:6379/0

# Run Dev Server (Auto-starts API + Worker + Flower)
uv run genpulse dev
```

## 📚 Documentation

See `docs/` for detailed guides:
*   [API Reference](docs/api.md)
*   [Deployment Guide](docs/deploy.md)
*   [Java Integration](docs/dev/java_integration.md)

## 🧩 Architecture

GenPulse uses a decoupled architecture:
1.  **API Gateway (FastAPI)**: Validates requests and pushes to Redis/Celery.
2.  **Task Workers (Celery)**: Async consumers that execute long-running AI tasks.
3.  **Unified Storage**: Abstracts local fs vs S3/OSS.
4.  **Database (Postgres)**: Durable state storage for tasks.

## License

MIT
